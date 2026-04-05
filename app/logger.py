#!/usr/bin/env python3
"""
日志配置模块
提供全局日志记录器
"""

import logging
import sys
from typing import Optional


def setup_logger(
    log_level: str = "INFO",
    name: str = "multimodal_inpainting",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        name: 日志记录器名称
        log_file: 可选日志文件路径

    Returns:
        配置好的日志记录器
    """
    # 获取日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 创建记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除现有处理器（避免重复）
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果提供了日志文件）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 防止日志传递给根记录器
    logger.propagate = False

    return logger


# 全局日志记录器实例
_logger_instance: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局日志记录器（如果未初始化则使用默认配置）"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = setup_logger()
    return _logger_instance