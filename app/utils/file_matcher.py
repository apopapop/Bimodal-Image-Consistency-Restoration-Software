#!/usr/bin/env python3
"""
文件匹配模块
扫描可见光目录，查找对应的红外图像，返回图像对列表
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging


@dataclass
class ImagePair:
    """可见光-红外图像对"""
    vis_path: Path      # 可见光图像路径
    ir_path: Path       # 红外图像路径
    filename: str       # 文件名


class FileMatcher:
    """文件匹配器"""

    # 支持的图像扩展名
    SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")

    def __init__(self, vis_dir: Path, ir_dir: Path, logger: Optional[logging.Logger] = None):
        """
        初始化文件匹配器

        Args:
            vis_dir: 可见光图像目录
            ir_dir: 红外图像目录
            logger: 日志记录器（如果未提供则创建）
        """
        self.vis_dir = vis_dir
        self.ir_dir = ir_dir
        self.logger = logger or logging.getLogger(__name__)

    def find_pairs(self) -> List[ImagePair]:
        """
        查找所有匹配的图像对

        Returns:
            图像对列表，按文件名排序
        """
        self.logger.info(f"扫描可见光目录: {self.vis_dir}")
        self.logger.info(f"扫描红外目录: {self.ir_dir}")

        # 获取可见光文件列表
        vis_files = self._list_image_files(self.vis_dir)
        if not vis_files:
            self.logger.warning(f"在可见光目录中未找到图像文件: {self.vis_dir}")
            return []

        # 查找匹配的红外图像
        pairs_dict = {}  # 使用字典确保文件名唯一
        missing_count = 0

        for vis_path in vis_files:
            ir_path = self.ir_dir / vis_path.name

            if ir_path.exists() and ir_path.is_file():
                # 使用字典确保每个文件名只出现一次
                pairs_dict[vis_path.name] = ImagePair(vis_path, ir_path, vis_path.name)
            else:
                self.logger.warning(f"红外图像缺失: {vis_path.name}")
                missing_count += 1

        # 转换为列表并排序
        pairs = list(pairs_dict.values())
        pairs.sort(key=lambda p: p.filename)

        # 输出统计信息
        self.logger.info(f"找到 {len(pairs)} 对匹配图像，缺失 {missing_count} 张红外图像")

        return pairs

    def _list_image_files(self, directory: Path) -> List[Path]:
        """
        列出目录中所有支持的图像文件

        Args:
            directory: 目录路径

        Returns:
            图像文件路径列表
        """
        if not directory.exists():
            return []

        files = []
        for ext in self.SUPPORTED_EXTS:
            # 查找小写扩展名文件
            files.extend(directory.glob(f"*{ext}"))
            # 查找大写扩展名文件
            files.extend(directory.glob(f"*{ext.upper()}"))

        # 过滤掉目录，只保留文件
        files = [f for f in files if f.is_file()]

        # 去重（使用绝对路径，避免因为大小写或符号链接导致的重复）
        unique_files = []
        seen = set()
        for f in files:
            # 使用绝对路径和规范化路径来去重
            abs_path = f.resolve()
            if abs_path not in seen:
                seen.add(abs_path)
                unique_files.append(f)

        # 按文件名排序
        unique_files.sort(key=lambda f: f.name)
        return unique_files

    def validate_pair(self, vis_path: Path, ir_path: Path) -> bool:
        """
        验证图像对是否有效

        Args:
            vis_path: 可见光图像路径
            ir_path: 红外图像路径

        Returns:
            是否有效
        """
        if not vis_path.exists():
            self.logger.error(f"可见光图像不存在: {vis_path}")
            return False

        if not ir_path.exists():
            self.logger.error(f"红外图像不存在: {ir_path}")
            return False

        return True