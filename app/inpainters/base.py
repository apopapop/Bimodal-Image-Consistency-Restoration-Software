#!/usr/bin/env python3
"""
修复器基类模块
定义修复器抽象接口
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Optional
import logging


class BaseInpainter(ABC):
    """修复器基类"""

    def __init__(self, name: str = "BaseInpainter"):
        """
        初始化修复器

        Args:
            name: 修复器名称
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化修复器

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        修复图像

        Args:
            image: H×W×3 BGR图像 (uint8)
            mask: H×W 掩膜 (uint8, 0/255)

        Returns:
            修复后的BGR图像 (uint8)

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 修复过程失败
        """
        pass

    def is_available(self) -> bool:
        """
        检查修复器是否可用

        Returns:
            是否可用
        """
        return self._initialized

    def validate_inputs(self, image: np.ndarray, mask: np.ndarray) -> bool:
        """
        验证输入参数

        Args:
            image: 图像数据
            mask: 掩膜数据

        Returns:
            是否有效
        """
        # 检查图像
        if image is None or len(image.shape) != 3 or image.shape[2] != 3:
            self.logger.error(f"无效图像: 形状={image.shape if image is not None else 'None'}")
            return False

        # 检查掩膜
        if mask is None:
            self.logger.error("掩膜为None")
            return False

        # 掩膜可以是单通道或三通道
        if len(mask.shape) not in [2, 3]:
            self.logger.error(f"无效掩膜形状: {mask.shape}")
            return False

        # 检查尺寸匹配
        if image.shape[:2] != mask.shape[:2]:
            self.logger.error(
                f"图像和掩膜尺寸不匹配: 图像={image.shape[:2]}, 掩膜={mask.shape[:2]}"
            )
            return False

        return True

    def preprocess_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        预处理掩膜（确保为单通道0/255）

        Args:
            mask: 输入掩膜

        Returns:
            预处理后的掩膜
        """
        # 如果是三通道，转换为单通道
        if len(mask.shape) == 3:
            # 取第一个通道（假设所有通道值相同）
            mask = mask[:, :, 0]

        # 二值化处理
        _, mask_binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        return mask_binary


# 导入cv2供子类使用
import cv2