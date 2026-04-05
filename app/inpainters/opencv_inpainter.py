#!/usr/bin/env python3
"""
OpenCV修复器模块
使用OpenCV的inpaint函数进行图像修复
"""

import cv2
import numpy as np
from .base import BaseInpainter
from typing import Optional


class OpenCVInpainter(BaseInpainter):
    """OpenCV修复器"""

    # OpenCV修复方法
    METHODS = {
        "telea": cv2.INPAINT_TELEA,  # Telea算法（较快）
        "ns": cv2.INPAINT_NS,        # Navier-Stokes算法（质量较好）
    }

    def __init__(self, method: str = "telea", inpaint_radius: int = 3):
        """
        初始化OpenCV修复器

        Args:
            method: 修复方法 ("telea" 或 "ns")
            inpaint_radius: 修复半径
        """
        super().__init__(name="OpenCVInpainter")
        self.method = self.METHODS.get(method.lower(), cv2.INPAINT_TELEA)
        self.inpaint_radius = inpaint_radius
        self.logger.info(f"使用OpenCV修复方法: {method}, 半径: {inpaint_radius}")

    def initialize(self) -> bool:
        """
        初始化修复器（OpenCV始终可用）

        Returns:
            总是返回True
        """
        self._initialized = True
        self.logger.info("OpenCV修复器初始化成功")
        return True

    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        使用OpenCV修复图像

        Args:
            image: H×W×3 BGR图像 (uint8)
            mask: H×W 掩膜 (uint8, 0/255)

        Returns:
            修复后的BGR图像 (uint8)

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 修复过程失败
        """
        # 验证输入
        if not self.validate_inputs(image, mask):
            raise ValueError("输入参数无效")

        try:
            # 预处理掩膜
            mask_processed = self.preprocess_mask(mask)

            # 记录处理信息
            mask_pixels = np.sum(mask_processed > 0)
            total_pixels = mask_processed.size
            self.logger.debug(
                f"修复区域: {mask_pixels}像素 ({mask_pixels/total_pixels*100:.1f}%)"
            )

            # 执行修复
            self.logger.info("开始OpenCV修复...")
            result = cv2.inpaint(
                image,
                mask_processed,
                self.inpaint_radius,
                self.method
            )

            self.logger.info("OpenCV修复完成")
            return result

        except cv2.error as e:
            error_msg = f"OpenCV修复失败: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"修复过程发生意外错误: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def set_method(self, method: str) -> None:
        """
        设置修复方法

        Args:
            method: 修复方法 ("telea" 或 "ns")
        """
        if method.lower() in self.METHODS:
            self.method = self.METHODS[method.lower()]
            self.logger.info(f"修复方法已更改为: {method}")
        else:
            self.logger.warning(f"未知修复方法: {method}，使用默认方法")

    def set_inpaint_radius(self, radius: int) -> None:
        """
        设置修复半径

        Args:
            radius: 修复半径
        """
        self.inpaint_radius = max(1, radius)
        self.logger.info(f"修复半径已更改为: {radius}")