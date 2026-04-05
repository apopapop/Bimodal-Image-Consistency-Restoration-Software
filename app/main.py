#!/usr/bin/env python3
"""
主程序模块
命令行入口点
"""

import argparse
from pathlib import Path
import sys
import os

# 添加当前目录到Python路径（确保模块导入正常工作）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config, InpainterBackend, LamaMode
from app.logger import setup_logger
from app.inpainters.opencv_inpainter import OpenCVInpainter
from app.inpainters.lama_inpainter import LamaInpainter
from app.core.pipeline import InpaintingPipeline


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="多模态图像修复程序 (VIS + IR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # OpenCV后端 (调试用)
  python run.py --vis-dir dataset/visible --ir-dir dataset/infrared --out-dir output --backend opencv

  # LaMa后端 (ModelScope模式)
  python run.py --vis-dir dataset/visible --ir-dir dataset/infrared --out-dir output --backend lama --lama-mode modelscope

  # 自定义画笔大小
  python run.py --vis-dir dataset/visible --ir-dir dataset/infrared --out-dir output --brush-radius 30

  # 设置日志级别
  python run.py --vis-dir dataset/visible --ir-dir dataset/infrared --out-dir output --log-level DEBUG

环境变量:
  LAMA_REPO_PATH: 当使用 --lama-mode external_repo 时，需要设置此环境变量指向本地LaMa仓库
        """
    )

    # 必需参数
    required = parser.add_argument_group('必需参数')
    required.add_argument(
        "--vis-dir",
        type=Path,
        required=True,
        help="可见光图像目录"
    )
    required.add_argument(
        "--ir-dir",
        type=Path,
        required=True,
        help="红外图像目录"
    )
    required.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="输出目录"
    )

    # 修复后端参数
    backend = parser.add_argument_group('修复后端参数')
    backend.add_argument(
        "--backend",
        type=str,
        choices=["opencv", "lama"],
        default="opencv",
        help="修复后端 (默认: opencv)"
    )
    backend.add_argument(
        "--lama-mode",
        type=str,
        choices=["modelscope", "external_repo"],
        default="modelscope",
        help="LaMa运行模式 (默认: modelscope)"
    )
    backend.add_argument(
        "--lama-model-id",
        type=str,
        default="iic/cv_fft_inpainting_lama",
        help="ModelScope模型ID (默认: iic/cv_fft_inpainting_lama)"
    )

    # UI参数
    ui = parser.add_argument_group('UI参数')
    ui.add_argument(
        "--brush-radius",
        type=int,
        default=20,
        help="画笔半径 (默认: 20)"
    )
    ui.add_argument(
        "--max-display-width",
        type=int,
        default=1024,
        help="最大显示宽度 (默认: 1024)"
    )
    ui.add_argument(
        "--max-display-height",
        type=int,
        default=768,
        help="最大显示高度 (默认: 768)"
    )

    # 其他参数
    other = parser.add_argument_group('其他参数')
    other.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别 (默认: INFO)"
    )
    other.add_argument(
        "--log-file",
        type=Path,
        help="日志文件路径 (可选)"
    )

    return parser.parse_args()


def create_config(args: argparse.Namespace) -> Config:
    """
    创建配置对象

    Args:
        args: 命令行参数

    Returns:
        配置对象
    """
    config = Config(
        vis_dir=args.vis_dir,
        ir_dir=args.ir_dir,
        output_dir=args.out_dir,
        backend=InpainterBackend(args.backend),
        lama_mode=LamaMode(args.lama_mode),
        lama_model_id=args.lama_model_id,
        brush_radius=args.brush_radius,
        max_display_size=(args.max_display_width, args.max_display_height),
        log_level=args.log_level
    )

    return config


def create_inpainter(config: Config, logger) -> OpenCVInpainter | LamaInpainter:
    """
    创建修复器实例

    Args:
        config: 程序配置
        logger: 日志记录器

    Returns:
        修复器实例

    Raises:
        RuntimeError: 修复器创建失败
    """
    if config.backend == InpainterBackend.OPENCV:
        logger.info("使用 OpenCV 修复后端")
        inpainter = OpenCVInpainter()
        if not inpainter.initialize():
            raise RuntimeError("OpenCV修复器初始化失败")
        return inpainter

    elif config.backend == InpainterBackend.LAMA:
        logger.info(f"使用 LaMa 修复后端 (模式: {config.lama_mode.value})")

        # 创建LaMa修复器
        inpainter = LamaInpainter(
            mode=config.lama_mode.value,
            model_id=config.lama_model_id,
            use_gpu=True
        )

        # 尝试初始化
        if inpainter.initialize():
            logger.info("LaMa 初始化成功")
            return inpainter
        else:
            logger.warning("LaMa 初始化失败，回退到 OpenCV")
            fallback = OpenCVInpainter()
            if not fallback.initialize():
                raise RuntimeError("OpenCV修复器初始化失败")
            return fallback

    else:
        raise ValueError(f"未知的修复后端: {config.backend}")


def validate_directories(config: Config, logger) -> bool:
    """
    验证目录是否存在

    Args:
        config: 程序配置
        logger: 日志记录器

    Returns:
        目录是否有效
    """
    # 验证输入目录
    if not config.vis_dir.exists():
        logger.error(f"可见光目录不存在: {config.vis_dir}")
        return False

    if not config.ir_dir.exists():
        logger.error(f"红外目录不存在: {config.ir_dir}")
        return False

    # 检查目录是否为空
    vis_files = list(config.vis_dir.glob("*"))
    if not vis_files:
        logger.warning(f"可见光目录为空: {config.vis_dir}")

    ir_files = list(config.ir_dir.glob("*"))
    if not ir_files:
        logger.warning(f"红外目录为空: {config.ir_dir}")

    return True


def main() -> int:
    """
    主函数

    Returns:
        退出代码 (0成功，非0失败)
    """
    # 解析参数
    args = parse_arguments()

    # 初始化日志
    logger = setup_logger(args.log_level, log_file=args.log_file)

    try:
        # 显示程序信息
        logger.info("=" * 60)
        logger.info("多模态图像修复程序")
        logger.info("=" * 60)
        logger.info(f"可见光目录: {args.vis_dir}")
        logger.info(f"红外目录: {args.ir_dir}")
        logger.info(f"输出目录: {args.out_dir}")
        logger.info(f"修复后端: {args.backend} ({args.lama_mode})")

        # 创建配置
        config = create_config(args)

        # 验证目录
        if not validate_directories(config, logger):
            return 1

        # 创建修复器
        logger.info("初始化修复器...")
        inpainter = create_inpainter(config, logger)

        # 创建并运行处理流水线
        logger.info("创建处理流水线...")
        pipeline = InpaintingPipeline(config, logger, inpainter)

        logger.info("开始处理流程...")
        success = pipeline.run()

        if success:
            logger.info("程序执行成功")
            return 0
        else:
            logger.error("程序执行失败")
            return 1

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        return 130  # SIGINT退出代码
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())