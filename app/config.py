#!/usr/bin/env python3
"""
配置管理模块
定义程序配置参数和数据结构
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import enum


class InpainterBackend(enum.Enum):
    """修复后端类型"""
    OPENCV = "opencv"
    LAMA = "lama"


class LamaMode(enum.Enum):
    """LaMa运行模式"""
    MODELSCOPE = "modelscope"
    EXTERNAL_REPO = "external_repo"


@dataclass
class Config:
    """程序配置"""
    # 目录路径
    vis_dir: Path           # 可见光图像目录
    ir_dir: Path            # 红外图像目录
    output_dir: Path        # 输出根目录

    # 修复后端配置
    backend: InpainterBackend = InpainterBackend.OPENCV
    lama_mode: LamaMode = LamaMode.MODELSCOPE
    lama_model_id: str = "iic/cv_fft_inpainting_lama"

    # UI配置
    brush_radius: int = 20
    max_display_size: tuple[int, int] = (1024, 768)

    # 处理配置
    log_level: str = "INFO"

    # 临时状态（运行时设置）
    filename: Optional[str] = None  # 当前处理的文件名

    # 输出目录子路径（计算属性）
    @property
    def output_vis_dir(self) -> Path:
        """可见光输出目录"""
        return self.output_dir / "visible"

    @property
    def output_ir_dir(self) -> Path:
        """红外输出目录"""
        return self.output_dir / "infrared"

    @property
    def output_mask_dir(self) -> Path:
        """掩膜输出目录"""
        return self.output_dir / "masks"

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.vis_dir.exists():
            raise ValueError(f"可见光目录不存在: {self.vis_dir}")
        if not self.ir_dir.exists():
            raise ValueError(f"红外目录不存在: {self.ir_dir}")
        return True