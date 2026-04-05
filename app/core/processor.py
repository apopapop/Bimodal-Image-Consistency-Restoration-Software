#!/usr/bin/env python3
"""
处理器模块
处理单个可见光-红外图像对
"""

from pathlib import Path
import numpy as np
import logging
import time
from typing import Optional, Tuple

from app.utils.file_matcher import ImagePair
from app.utils.image import ImageUtils
from app.utils.io import IOUtils
from app.ui.mask_editor import MaskEditor
from app.inpainters.base import BaseInpainter


class ImageProcessor:
    """图像处理器"""

    def __init__(
        self,
        config,
        logger: logging.Logger,
        inpainter: BaseInpainter
    ):
        """
        初始化图像处理器

        Args:
            config: 程序配置
            logger: 日志记录器
            inpainter: 修复器实例
        """
        self.config = config
        self.logger = logger
        self.inpainter = inpainter
        self.mask_editor = MaskEditor(config, logger)

        self.logger.debug("图像处理器初始化完成")

    def process_pair(self, pair: ImagePair) -> bool:
        """
        处理单个图像对

        Args:
            pair: 图像对

        Returns:
            是否成功处理
        """
        self.logger.info(f"开始处理: {pair.filename}")

        try:
            # 1. 加载图像
            vis_img, ir_img = self._load_images(pair)
            if vis_img is None or ir_img is None:
                return False

            # 2. 检查图像尺寸
            if not self._validate_image_sizes(vis_img, ir_img, pair.filename):
                return False

            # 3. 运行掩膜编辑器
            mask = self._run_mask_editor(vis_img, pair.filename)
            if mask is None:
                # 用户跳过或取消
                return False

            # 4. 应用修复
            vis_result, ir_result = self._apply_inpainting(vis_img, ir_img, mask, pair.filename)
            if vis_result is None or ir_result is None:
                return False

            # 5. 保存结果
            success = self._save_results(pair, vis_result, ir_result, mask)
            if success:
                self.logger.info(f"处理完成: {pair.filename}")
            else:
                self.logger.error(f"保存结果失败: {pair.filename}")

            return success

        except Exception as e:
            self.logger.error(f"处理图像对失败 {pair.filename}: {e}", exc_info=True)
            return False

    def _load_images(self, pair: ImagePair) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        加载可见光和红外图像

        Args:
            pair: 图像对

        Returns:
            (可见光图像, 红外图像)，失败时返回(None, None)
        """
        try:
            self.logger.info(f"加载可见光图像: {pair.vis_path}")
            vis_img = ImageUtils.load_image(pair.vis_path)

            self.logger.info(f"加载红外图像: {pair.ir_path}")
            ir_img = ImageUtils.load_image(pair.ir_path)

            return vis_img, ir_img

        except ValueError as e:
            self.logger.error(f"加载图像失败 {pair.filename}: {e}")
            return None, None
        except Exception as e:
            self.logger.error(f"加载图像时发生意外错误 {pair.filename}: {e}")
            return None, None

    def _validate_image_sizes(
        self,
        vis_img: np.ndarray,
        ir_img: np.ndarray,
        filename: str
    ) -> bool:
        """
        验证图像尺寸是否匹配

        Args:
            vis_img: 可见光图像
            ir_img: 红外图像
            filename: 文件名

        Returns:
            尺寸是否匹配
        """
        if not ImageUtils.check_size_match(vis_img, ir_img):
            self.logger.error(f"图像尺寸不匹配 {filename}: "
                            f"VIS={vis_img.shape[:2]}, IR={ir_img.shape[:2]}")
            return False

        self.logger.debug(f"图像尺寸验证通过: {vis_img.shape[:2]}")
        return True

    def _run_mask_editor(
        self,
        vis_img: np.ndarray,
        filename: str
    ) -> Optional[np.ndarray]:
        """
        运行掩膜编辑器

        Args:
            vis_img: 可见光图像
            filename: 文件名

        Returns:
            掩膜或None（用户跳过/切换/退出）
        """
        # 设置当前文件名（用于显示）
        self.config.filename = filename

        self.logger.info("启动掩膜编辑器...")
        result = self.mask_editor.run(vis_img)

        # 处理特殊动作
        if isinstance(result, str):
            self.logger.info(f"收到特殊动作: {result} (文件: {filename})")
            if result == "prev":
                self.logger.info(f"用户请求上一张图像: {filename}")
                # 设置特殊状态，让pipeline知道要切换到上一张
                setattr(self.config, "_requested_action", "prev")
            elif result == "next" or result == "skip":
                # "skip"和"next"都表示切换到下一张
                action = "next" if result == "next" else "skip"
                self.logger.info(f"用户请求{action}图像: {filename}")
                # 设置特殊状态，让pipeline知道要切换到下一张
                setattr(self.config, "_requested_action", action)
            elif result == "quit":
                self.logger.info(f"用户退出程序: {filename}")
                # 设置退出标志
                setattr(self.config, "_requested_action", "quit")
            else:
                self.logger.warning(f"未知的特殊动作: {result}")
            return None

        # 正常返回掩膜或None
        if result is None:
            self.logger.info(f"用户跳过图像: {filename}")
            return None

        # 检查掩膜是否为空
        if not np.any(result > 0):
            self.logger.info(f"掩膜为空，跳过图像: {filename}")
            return None

        mask_pixels = np.sum(result > 0)
        total_pixels = result.size
        percentage = mask_pixels / total_pixels * 100
        self.logger.info(f"掩膜区域: {mask_pixels}像素 ({percentage:.1f}%)")

        return result

    def _apply_inpainting(
        self,
        vis_img: np.ndarray,
        ir_img: np.ndarray,
        mask: np.ndarray,
        filename: str
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        应用修复

        Args:
            vis_img: 可见光图像
            ir_img: 红外图像
            mask: 掩膜
            filename: 文件名

        Returns:
            (修复后的可见光图像, 修复后的红外图像)
        """
        try:
            # 修复可见光图像
            self.logger.info(f"修复可见光图像: {filename}")
            start_time = time.time()
            vis_result = self.inpainter.inpaint(vis_img, mask)
            vis_time = time.time() - start_time
            self.logger.info(f"可见光图像修复完成，耗时: {vis_time:.2f}s")

            # 修复红外图像（使用相同掩膜）
            self.logger.info(f"修复红外图像: {filename}")
            start_time = time.time()
            ir_result = self.inpainter.inpaint(ir_img, mask)
            ir_time = time.time() - start_time
            self.logger.info(f"红外图像修复完成，耗时: {ir_time:.2f}s")

            # 验证修复结果
            if vis_result is None or ir_result is None:
                self.logger.error(f"修复结果为空: {filename}")
                return None, None

            if vis_result.shape != vis_img.shape or ir_result.shape != ir_img.shape:
                self.logger.warning(f"修复结果尺寸变化: {filename}")

            return vis_result, ir_result

        except Exception as e:
            self.logger.error(f"修复过程失败 {filename}: {e}", exc_info=True)
            return None, None

    def _save_results(
        self,
        pair: ImagePair,
        vis_result: np.ndarray,
        ir_result: np.ndarray,
        mask: np.ndarray
    ) -> bool:
        """
        保存所有结果文件

        Args:
            pair: 图像对
            vis_result: 修复后的可见光图像
            ir_result: 修复后的红外图像
            mask: 使用的掩膜

        Returns:
            是否全部保存成功
        """
        # 准备输出目录
        if not IOUtils.prepare_output_dirs(self.config.output_dir):
            self.logger.error(f"创建输出目录失败: {self.config.output_dir}")
            return False

        # 生成输出路径
        vis_output = self.config.output_vis_dir / pair.filename
        ir_output = self.config.output_ir_dir / pair.filename

        # 掩膜文件名
        mask_stem = Path(pair.filename).stem
        mask_output = self.config.output_mask_dir / f"{mask_stem}_mask.png"

        self.logger.info(f"保存结果文件:")
        self.logger.info(f"  - 可见光: {vis_output}")
        self.logger.info(f"  - 红外: {ir_output}")
        self.logger.info(f"  - 掩膜: {mask_output}")

        # 保存文件
        success = True

        if not IOUtils.save_image(vis_result, vis_output):
            self.logger.error(f"保存可见光图像失败: {vis_output}")
            success = False

        if not IOUtils.save_image(ir_result, ir_output):
            self.logger.error(f"保存红外图像失败: {ir_output}")
            success = False

        if not IOUtils.save_mask(mask, mask_output):
            self.logger.error(f"保存掩膜失败: {mask_output}")
            success = False

        return success

    def get_inpainter_info(self) -> dict:
        """获取修复器信息"""
        if hasattr(self.inpainter, 'get_model_info'):
            return self.inpainter.get_model_info()
        else:
            return {
                "name": self.inpainter.name,
                "available": self.inpainter.is_available()
            }