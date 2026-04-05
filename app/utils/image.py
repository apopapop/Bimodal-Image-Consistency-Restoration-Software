#!/usr/bin/env python3
"""
图像处理工具模块
提供图像加载、转换、验证等功能
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging


class ImageUtils:
    """图像处理工具类"""

    @staticmethod
    def load_image(path: Path) -> np.ndarray:
        """
        加载图像并转换为BGR三通道格式

        Args:
            path: 图像文件路径

        Returns:
            BGR三通道图像 (H×W×3, uint8)

        Raises:
            ValueError: 图像加载失败或不支持格式
        """
        # 使用IMREAD_UNCHANGED保留原始通道信息
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"无法加载图像: {path}")

        # 记录原始形状
        logging.debug(f"加载图像 {path.name}: 形状={img.shape}, 类型={img.dtype}")

        # 处理不同通道数的图像
        if len(img.shape) == 2:
            # 单通道图像 -> 转为三通道
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            logging.debug(f"单通道图像转换为三通道: {path.name}")

        elif img.shape[2] == 4:
            # 四通道图像 (BGRA) -> 移除alpha通道
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            logging.debug(f"四通道图像移除alpha通道: {path.name}")

        elif img.shape[2] == 3:
            # 已为三通道图像，假设为BGR
            pass

        else:
            raise ValueError(f"不支持的通道数: {img.shape} (路径: {path})")

        return img

    @staticmethod
    def check_size_match(img1: np.ndarray, img2: np.ndarray) -> bool:
        """
        检查两张图像尺寸是否匹配

        Args:
            img1: 第一张图像
            img2: 第二张图像

        Returns:
            尺寸是否匹配
        """
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        return h1 == h2 and w1 == w2

    @staticmethod
    def resize_to_fit(img: np.ndarray, max_size: Tuple[int, int]) -> np.ndarray:
        """
        调整图像尺寸以适应显示窗口

        Args:
            img: 输入图像
            max_size: 最大尺寸 (宽, 高)

        Returns:
            调整后的图像
        """
        h, w = img.shape[:2]
        max_w, max_h = max_size

        # 如果图像尺寸小于等于最大尺寸，直接返回
        if w <= max_w and h <= max_h:
            return img

        # 计算缩放比例
        scale = min(max_w / w, max_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # 调整尺寸
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logging.debug(f"图像尺寸调整: {w}x{h} -> {new_w}x{new_h}")

        return resized

    @staticmethod
    def create_mask_overlay(image: np.ndarray, mask: np.ndarray, alpha: float = 0.3) -> np.ndarray:
        """
        创建掩膜覆盖层（半透明红色）

        Args:
            image: 原始图像 (BGR)
            mask: 二值掩膜 (0/255)
            alpha: 覆盖层透明度 (0-1)

        Returns:
            带有掩膜覆盖的图像
        """
        # 创建红色覆盖层
        overlay = image.copy()
        red_mask = np.zeros_like(image)
        red_mask[:, :, 2] = 255  # 红色通道 (BGR中的R通道)

        # 将掩膜区域设置为红色
        mask_bool = mask > 0
        overlay[mask_bool] = red_mask[mask_bool]

        # 混合原始图像和覆盖层
        result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)
        return result

    @staticmethod
    def ensure_3channel(image: np.ndarray) -> np.ndarray:
        """
        确保图像为三通道BGR格式

        Args:
            image: 输入图像

        Returns:
            三通道BGR图像
        """
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        elif image.shape[2] == 3:
            return image
        else:
            raise ValueError(f"不支持的图像形状: {image.shape}")

    @staticmethod
    def mask_to_3channel(mask: np.ndarray) -> np.ndarray:
        """
        将单通道掩膜转换为三通道

        Args:
            mask: 单通道掩膜 (0/255)

        Returns:
            三通道掩膜
        """
        if len(mask.shape) == 2:
            return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        return mask