#!/usr/bin/env python3
"""
I/O工具模块
提供目录创建、文件保存等功能
"""

from pathlib import Path
import cv2
import numpy as np
import logging
from typing import Optional


class IOUtils:
    """I/O工具类"""

    @staticmethod
    def ensure_dir(path: Path) -> bool:
        """
        确保目录存在，如果不存在则创建

        Args:
            path: 目录路径

        Returns:
            是否成功
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败 {path}: {e}")
            return False

    @staticmethod
    def save_image(
        img: np.ndarray,
        path: Path,
        quality: Optional[int] = None
    ) -> bool:
        """
        保存图像，保留原始格式

        Args:
            img: 图像数据 (BGR格式)
            path: 保存路径
            quality: JPEG质量 (1-100)，仅对JPEG有效

        Returns:
            是否成功
        """
        try:
            # 准备保存参数
            params = []
            if path.suffix.lower() in ['.jpg', '.jpeg'] and quality is not None:
                params = [cv2.IMWRITE_JPEG_QUALITY, max(1, min(100, quality))]

            # 保存图像
            success = cv2.imwrite(str(path), img, params)
            if success:
                logging.debug(f"图像保存成功: {path}")
            else:
                logging.error(f"图像保存失败: {path}")
            return success

        except Exception as e:
            logging.error(f"保存图像失败 {path}: {e}")
            return False

    @staticmethod
    def save_mask(mask: np.ndarray, path: Path) -> bool:
        """
        保存掩膜为PNG格式（无损）

        Args:
            mask: 掩膜数据 (0/255)
            path: 保存路径

        Returns:
            是否成功
        """
        try:
            # 确保路径以.png结尾
            if path.suffix.lower() != '.png':
                path = path.with_suffix('.png')

            # 保存掩膜（PNG无损压缩）
            success = cv2.imwrite(str(path), mask)
            if success:
                logging.debug(f"掩膜保存成功: {path}")
            else:
                logging.error(f"掩膜保存失败: {path}")
            return success

        except Exception as e:
            logging.error(f"保存掩膜失败 {path}: {e}")
            return False

    @staticmethod
    def generate_output_paths(
        base_dir: Path,
        filename: str,
        mask_suffix: str = "_mask"
    ) -> tuple[Path, Path, Path]:
        """
        生成输出文件路径

        Args:
            base_dir: 基础输出目录
            filename: 原始文件名
            mask_suffix: 掩膜文件后缀

        Returns:
            (vis_output_path, ir_output_path, mask_output_path)
        """
        # 创建子目录路径
        vis_dir = base_dir / "visible"
        ir_dir = base_dir / "infrared"
        mask_dir = base_dir / "masks"

        # 生成输出路径
        vis_output = vis_dir / filename
        ir_output = ir_dir / filename

        # 掩膜文件使用PNG格式
        stem = Path(filename).stem
        mask_output = mask_dir / f"{stem}{mask_suffix}.png"

        return vis_output, ir_output, mask_output

    @staticmethod
    def prepare_output_dirs(base_dir: Path) -> bool:
        """
        准备输出目录结构

        Args:
            base_dir: 基础输出目录

        Returns:
            是否成功
        """
        dirs = [
            base_dir / "visible",
            base_dir / "infrared",
            base_dir / "masks"
        ]

        success = True
        for dir_path in dirs:
            if not IOUtils.ensure_dir(dir_path):
                success = False

        return success

    @staticmethod
    def read_mask(path: Path) -> Optional[np.ndarray]:
        """
        读取掩膜文件

        Args:
            path: 掩膜文件路径

        Returns:
            掩膜数据 (0/255)，失败返回None
        """
        try:
            mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                logging.error(f"无法读取掩膜文件: {path}")
                return None

            # 二值化处理（确保为0/255）
            _, mask_binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            return mask_binary

        except Exception as e:
            logging.error(f"读取掩膜失败 {path}: {e}")
            return None