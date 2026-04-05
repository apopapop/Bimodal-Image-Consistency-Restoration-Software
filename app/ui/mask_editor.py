#!/usr/bin/env python3
"""
掩膜编辑器模块
提供OpenCV交互式掩膜绘制功能
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import logging
import sys


class MaskEditor:
    """OpenCV交互式掩膜编辑器"""

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """
        初始化掩膜编辑器

        Args:
            config: 程序配置对象
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # 状态变量
        self.mask: Optional[np.ndarray] = None
        self.vis_image: Optional[np.ndarray] = None
        self.undo_stack: List[np.ndarray] = []
        self.is_drawing = False
        self.last_point: Optional[Tuple[int, int]] = None
        self.brush_radius = config.brush_radius

        # 显示窗口名称
        self.window_name = "Multimodal Inpainting - Draw on VIS"
        self.logger.debug("掩膜编辑器初始化完成")

    def run(self, vis_image: np.ndarray) -> Optional[np.ndarray]:
        """
        运行编辑器，允许用户在可见光图像上绘制掩膜

        Args:
            vis_image: 可见光图像 (BGR格式)

        Returns:
            最终掩膜 (如果用户确认) 或 None (如果用户跳过/取消) 或 特殊动作字符串:
            - "prev": 用户请求上一张图像
            - "next": 用户请求下一张图像
            - "quit": 用户退出程序
        """
        self.vis_image = vis_image.copy()
        h, w = vis_image.shape[:2]

        # 初始化掩膜
        self.mask = np.zeros((h, w), dtype=np.uint8)
        self.undo_stack.clear()
        self.is_drawing = False
        self.last_point = None

        # 创建显示窗口
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)

        self.logger.info("掩膜编辑器已启动，等待用户绘制...")

        # 主循环
        special_action = None
        while True:
            # 创建显示图像
            display = self._create_display()

            # 显示图像
            cv2.imshow(self.window_name, display)

            # 处理键盘事件 - 使用waitKeyEx获取扩展键码
            raw_key = cv2.waitKeyEx(30)  # 使用waitKeyEx以支持方向键等扩展键
            if raw_key == -1:
                # 没有按键
                action = ""
                key = -1
            else:
                # 对于普通键，使用低8位；对于特殊键，可能需要检查原始值
                key = raw_key & 0xFF
                # 调试：记录所有按键
                self.logger.debug(f"收到按键: raw={raw_key}, key={key}, hex={hex(raw_key)}")
                action = self._handle_key(key, raw_key)
                # 调试：记录特殊按键
                if action in ["prev", "next", "quit"]:
                    self.logger.debug(f"检测到特殊动作: action={action}")

            # 根据动作决定下一步
            if action == "quit":
                self.logger.info("用户退出编辑器")
                self.mask = None
                special_action = "quit"
                break
            elif action == "confirm":
                self.logger.info("用户确认掩膜")
                break
            elif action == "skip":
                self.logger.info("用户跳过当前图像")
                self.mask = None
                break
            elif action == "prev":
                self.logger.info("用户请求上一张图像")
                self.mask = None
                special_action = "prev"
                break
            elif action == "next":
                self.logger.info("用户请求下一张图像")
                self.mask = None
                special_action = "next"
                break

            # 检查窗口是否被关闭
            try:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 0.5:
                    self.logger.info("用户关闭了编辑器窗口")
                    self.mask = None
                    break
            except:
                # 窗口可能已经被销毁
                self.logger.info("编辑器窗口已关闭")
                self.mask = None
                break

        # 清理窗口
        try:
            cv2.destroyWindow(self.window_name)
            cv2.waitKey(1)  # 确保窗口关闭
        except:
            pass  # 窗口可能已经关闭

        # 如果有特殊动作，返回它
        if special_action is not None:
            return special_action

        # 返回结果
        if self.mask is None:
            self.logger.info("用户跳过当前图像")
            return None

        # 检查掩膜是否为空
        if not np.any(self.mask > 0):
            self.logger.info("掩膜为空，跳过当前图像")
            return None

        mask_pixels = np.sum(self.mask > 0)
        self.logger.info(f"掩膜绘制完成，选中区域: {mask_pixels}像素")
        return self.mask.copy()

    def _create_display(self) -> np.ndarray:
        """
        创建显示图像（原图 + 半透明掩膜覆盖 + 状态信息）

        Returns:
            显示图像
        """
        if self.vis_image is None or self.mask is None:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        # 创建掩膜覆盖层
        overlay = self.vis_image.copy()
        red_mask = np.zeros_like(self.vis_image)
        red_mask[:, :, 2] = 255  # 红色通道 (BGR中的R通道)

        # 将掩膜区域设置为红色
        mask_bool = self.mask > 0
        overlay[mask_bool] = red_mask[mask_bool]

        # 混合原始图像和覆盖层 (30%透明度)
        display = cv2.addWeighted(self.vis_image, 0.7, overlay, 0.3, 0)

        # 添加状态信息
        self._add_status_text(display)

        # 添加画笔预览（跟随鼠标）
        if self.last_point:
            x, y = self.last_point
            cv2.circle(display, (x, y), self.brush_radius, (0, 255, 0), 1)

        return display

    def _add_status_text(self, display: np.ndarray) -> None:
        """添加状态文本到显示图像"""
        h, w = display.shape[:2]

        # 背景矩形
        cv2.rectangle(display, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.rectangle(display, (0, 0), (w, 80), (100, 100, 100), 1)

        # 文件名
        filename = self.config.filename or "Unknown"
        file_text = f"File: {filename}"
        cv2.putText(
            display, file_text,
            (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (255, 255, 255), 2
        )

        # 画笔大小
        brush_text = f"Brush: {self.brush_radius}px"
        cv2.putText(
            display, brush_text,
            (10, 55), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (255, 255, 255), 2
        )

        # 掩膜统计
        if self.mask is not None:
            mask_pixels = np.sum(self.mask > 0)
            total_pixels = self.mask.size
            percent = mask_pixels / total_pixels * 100
            mask_text = f"Mask: {mask_pixels}px ({percent:.1f}%)"
            cv2.putText(
                display, mask_text,
                (w - 300, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 255), 1
            )

        # 快捷键提示
        help_text = "Drag: draw | u: undo | c: clear | +/-: brush | ↑/↓/w/s: prev/next | Enter: confirm | n: skip | q: quit"
        cv2.putText(
            display, help_text,
            (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.4, (150, 150, 150), 1
        )

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param) -> None:
        """
        鼠标事件回调函数

        Args:
            event: OpenCV鼠标事件
            x, y: 鼠标坐标
            flags: 事件标志
            param: 额外参数
        """
        # 确保坐标在图像范围内
        h, w = self.mask.shape[:2] if self.mask is not None else (0, 0)
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))

        if event == cv2.EVENT_LBUTTONDOWN:
            # 开始绘制
            self.is_drawing = True
            self._save_to_undo()
            self._draw_point(x, y)
            self.last_point = (x, y)
            self.logger.debug(f"开始绘制 at ({x}, {y})")

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.is_drawing and self.last_point:
                # 绘制线条
                self._draw_line(self.last_point, (x, y))
                self.last_point = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            # 停止绘制
            self.is_drawing = False
            self.last_point = None
            self.logger.debug("停止绘制")

        elif event == cv2.EVENT_MOUSEWHEEL:
            # 鼠标滚轮调整画笔大小
            if flags > 0:  # 向上滚动
                self.brush_radius = min(self.brush_radius + 2, 100)
            else:  # 向下滚动
                self.brush_radius = max(self.brush_radius - 2, 1)
            self.logger.debug(f"画笔大小调整为: {self.brush_radius}px")

    def _draw_point(self, x: int, y: int) -> None:
        """在掩膜上绘制一个点"""
        cv2.circle(self.mask, (x, y), self.brush_radius, 255, -1)

    def _draw_line(self, pt1: Tuple[int, int], pt2: Tuple[int, int]) -> None:
        """在掩膜上绘制一条线"""
        cv2.line(self.mask, pt1, pt2, 255, self.brush_radius * 2)

    def _save_to_undo(self) -> None:
        """保存当前掩膜到撤销栈"""
        if self.mask is not None:
            self.undo_stack.append(self.mask.copy())
            # 限制栈大小
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)

    def _handle_key(self, key: int, raw_key: int) -> str:
        """
        处理键盘事件

        Args:
            key: 按键代码（与0xFF进行AND操作后的值）
            raw_key: 原始按键代码

        Returns:
            动作字符串:
            - "undo": 撤销
            - "clear": 清空
            - "brush_up": 增大画笔
            - "brush_down": 减小画笔
            - "confirm": 确认掩膜
            - "skip": 跳过当前图像
            - "prev": 上一张图像
            - "next": 下一张图像
            - "quit": 退出程序
            - "": 无动作
        """
        # 调试：记录所有非空按键
        if raw_key != -1:
            self.logger.debug(f"按键检测: raw_key={raw_key}, key={key}, hex(raw_key)={hex(raw_key)}")

        if key == ord('u'):  # 撤销
            self._undo()
            return "undo"

        elif key == ord('c'):  # 清空
            self._clear()
            return "clear"

        elif key in (ord('+'), ord('=')):  # 增大画笔
            self.brush_radius = min(self.brush_radius + 2, 100)
            self.logger.debug(f"画笔大小增加至: {self.brush_radius}px")
            return "brush_up"

        elif key == ord('-'):  # 减小画笔
            self.brush_radius = max(self.brush_radius - 2, 1)
            self.logger.debug(f"画笔大小减小至: {self.brush_radius}px")
            return "brush_down"

        elif key == 13:  # Enter键 - 确认
            return "confirm"

        elif key == ord('n'):  # n键 - 跳过
            return "skip"

        # 检查方向键 - OpenCV在不同平台上的键值不同
        # 首先检查最常见的Windows和Linux键值
        if raw_key == 2490368 or raw_key == 65362 or raw_key == 82:  # 上方向键
            self.logger.debug(f"检测到上方向键: {raw_key}")
            return "prev"
        elif raw_key == 2621440 or raw_key == 65364 or raw_key == 84:  # 下方向键
            self.logger.debug(f"检测到下方向键: {raw_key}")
            return "next"

        # 检查扩展键值（Windows上某些系统）
        # 有时方向键返回类似 0xE048 (上) 或 0xE050 (下) 的值
        # 高位字节是 0xE0，低位字节是键码
        if (raw_key >> 8) & 0xFF == 0xE0:
            # 扩展键，检查低位字节
            low_byte = raw_key & 0xFF
            if low_byte == 0x48:  # 上方向键
                self.logger.debug(f"检测到扩展上方向键: raw_key={raw_key}")
                return "prev"
            elif low_byte == 0x50:  # 下方向键
                self.logger.debug(f"检测到扩展下方向键: raw_key={raw_key}")
                return "next"
            elif low_byte == 0x49:  # Page Up键
                self.logger.debug(f"检测到Page Up键: raw_key={raw_key}")
                return "prev"
            elif low_byte == 0x51:  # Page Down键
                self.logger.debug(f"检测到Page Down键: raw_key={raw_key}")
                return "next"

        # 检查其他可能的方向键表示
        # 在某些系统上，raw_key可能是类似 0x26 (38) 或 0x28 (40) 的值
        # 这些是Windows虚拟键码：VK_UP=0x26 (38), VK_DOWN=0x28 (40)
        if raw_key == 0x26 or raw_key == 38:
            self.logger.debug(f"检测到虚拟键码上方向键: {raw_key}")
            return "prev"
        elif raw_key == 0x28 or raw_key == 40:
            self.logger.debug(f"检测到虚拟键码下方向键: {raw_key}")
            return "next"

        # 检查Page Up/Page Down键（某些系统）
        if raw_key == 0x21 or raw_key == 33:  # Page Up
            self.logger.debug(f"检测到Page Up键: {raw_key}")
            return "prev"
        elif raw_key == 0x22 or raw_key == 34:  # Page Down
            self.logger.debug(f"检测到Page Down键: {raw_key}")
            return "next"

        # 检查低8位为0或1的特殊键（某些OpenCV版本）
        # 注意：在某些系统上，key=0可能表示上方向键，key=1可能表示下方向键
        # 但由于用户反馈方向键下时计数变化，我们调整策略：
        # 如果raw_key=0，可能是上方向键；如果raw_key=某个特定值，可能是下方向键
        # 这里我们添加更详细的调试
        if key == 0 and raw_key != -1:
            # 可能是上方向键或下方向键，需要进一步检查
            self.logger.debug(f"检测到key=0的特殊键，raw_key={raw_key} (hex: {hex(raw_key)})")
            # 检查是否是扩展键（虽然高位字节可能不是0xE0）
            high_byte = (raw_key >> 8) & 0xFF
            low_byte = raw_key & 0xFF
            self.logger.debug(f"  高位字节: {high_byte} (0x{high_byte:02X}), 低位字节: {low_byte} (0x{low_byte:02X})")

            # 根据用户反馈，方向键下时计数增加，可能被识别为next
            # 这里我们暂时保守地返回prev（上方向键）
            # 但添加特殊处理：如果raw_key有特定值，可能表示下方向键
            if raw_key == 0:
                self.logger.debug("raw_key=0，暂定为上方向键")
                return "prev"
            else:
                self.logger.debug(f"raw_key={raw_key}，暂定为下方向键")
                return "next"
        elif key == 1 and raw_key != -1:
            self.logger.debug(f"检测到key=1的特殊键，raw_key={raw_key} (hex: {hex(raw_key)})")
            return "next"

        # 备用键：w/s 或 W/S 用于上下导航
        if key == ord('w') or key == ord('W'):
            self.logger.debug(f"检测到备用上键: 'w'")
            return "prev"
        elif key == ord('s') or key == ord('S'):
            self.logger.debug(f"检测到备取下键: 's'")
            return "next"

        # 检查常见的退出键
        elif key in (27, ord('q')):  # Esc或q键 - 退出
            return "quit"

        return ""

    def _undo(self) -> None:
        """撤销上一步操作"""
        if self.undo_stack:
            self.mask = self.undo_stack.pop()
            self.logger.debug("撤销上一步操作")
        else:
            self.logger.debug("无可撤销的操作")

    def _clear(self) -> None:
        """清空所有绘制"""
        if self.mask is not None:
            self._save_to_undo()
            self.mask.fill(0)
            self.logger.debug("清空所有绘制")

    def get_mask_preview(self) -> Optional[np.ndarray]:
        """
        获取掩膜预览（掩膜区域为白色，背景为黑色）

        Returns:
            掩膜预览图像
        """
        if self.mask is None:
            return None
        return cv2.cvtColor(self.mask, cv2.COLOR_GRAY2BGR)