#!/usr/bin/env python3
"""
处理流水线模块
管理批处理流程
"""

from typing import List, Optional
import logging
import time

from app.utils.file_matcher import FileMatcher, ImagePair
from .processor import ImageProcessor
from app.inpainters.base import BaseInpainter


class InpaintingPipeline:
    """处理流水线"""

    def __init__(
        self,
        config,
        logger: logging.Logger,
        inpainter: BaseInpainter
    ):
        """
        初始化处理流水线

        Args:
            config: 程序配置
            logger: 日志记录器
            inpainter: 修复器实例
        """
        self.config = config
        self.logger = logger
        self.inpainter = inpainter
        self.processor = ImageProcessor(config, logger, inpainter)

        # 状态变量
        self.pairs: List[ImagePair] = []
        self.current_idx = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self.logger.debug("处理流水线初始化完成")

    def run(self) -> bool:
        """
        运行完整处理流程

        Returns:
            是否成功处理了至少一个图像对
        """
        self.start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info("开始多模态图像修复流程")
        self.logger.info("=" * 60)

        # 1. 查找图像对
        if not self._find_image_pairs():
            return False

        # 2. 显示修复器信息
        self._log_inpainter_info()

        # 3. 逐对处理
        success_count = self._process_all_pairs()

        # 4. 输出统计信息
        self._log_statistics(success_count)

        return success_count > 0

    def _find_image_pairs(self) -> bool:
        """
        查找所有匹配的图像对

        Returns:
            是否找到图像对
        """
        self.logger.info("扫描图像对...")

        try:
            matcher = FileMatcher(self.config.vis_dir, self.config.ir_dir, self.logger)
            self.pairs = matcher.find_pairs()

            if not self.pairs:
                self.logger.error("未找到匹配的图像对")
                return False

            self.logger.info(f"找到 {len(self.pairs)} 对图像 (共 {len(self.pairs) * 2} 张图片):")
            for i, pair in enumerate(self.pairs[:5]):  # 只显示前5对
                self.logger.info(f"  {i+1:3d}. {pair.filename}")
            if len(self.pairs) > 5:
                self.logger.info(f"  ... 以及 {len(self.pairs) - 5} 对更多图像")

            return True

        except Exception as e:
            self.logger.error(f"查找图像对失败: {e}", exc_info=True)
            return False

    def _log_inpainter_info(self) -> None:
        """记录修复器信息"""
        self.logger.info("修复器信息:")

        # 获取修复器信息
        info = self.processor.get_inpainter_info()
        for key, value in info.items():
            self.logger.info(f"  - {key}: {value}")

        self.logger.info(f"输出目录: {self.config.output_dir}")

    def _process_all_pairs(self) -> int:
        """
        处理所有图像对

        Returns:
            成功处理的图像对数量
        """
        total_count = len(self.pairs)
        success_count = 0
        skip_count = 0
        fail_count = 0

        self.logger.info(f"开始处理 {total_count} 对图像 (共 {total_count * 2} 张图片)...")

        # 使用while循环以便动态调整索引
        i = 0
        while i < total_count:
            pair = self.pairs[i]
            self.logger.info("-" * 40)
            self.logger.info(f"处理图像对 [{i+1}/{total_count}]: {pair.filename}")

            # 重置请求的动作
            if hasattr(self.config, "_requested_action"):
                delattr(self.config, "_requested_action")

            # 处理当前图像对
            success = self.processor.process_pair(pair)

            # 检查是否有特殊动作请求
            requested_action = None
            if hasattr(self.config, "_requested_action"):
                requested_action = getattr(self.config, "_requested_action")
                delattr(self.config, "_requested_action")

            # 处理特殊动作
            if requested_action == "quit":
                self.logger.info("用户请求退出程序")
                break
            elif requested_action == "prev":
                # 切换到上一张图像
                if i > 0:
                    i -= 1
                    self.logger.info(f"切换到上一张图像: {i+1}/{total_count}")
                    continue  # 继续处理上一张图像
                else:
                    self.logger.info("已经是第一张图像，无法切换到上一张")
            elif requested_action == "next" or requested_action == "skip":
                # 切换到下一张图像（相当于跳过当前）
                i += 1
                action_name = "切换" if requested_action == "next" else "跳过"
                self.logger.info(f"用户{action_name}当前图像，处理下一张: {i+1}/{total_count}")
                skip_count += 1
                self.logger.info(f"↷ 用户{action_name}: {pair.filename}")
                self._log_progress(i, total_count, success_count, skip_count, fail_count)
                continue

            # 更新统计
            if success:
                success_count += 1
                self.logger.info(f"✓ 处理成功: {pair.filename}")
            else:
                # 用户跳过或切换（已经在前面处理了requested_action == "next"的情况）
                # 这里处理普通的跳过或失败
                if requested_action is None:
                    # 普通跳过（按'n'键）
                    skip_count += 1
                    self.logger.info(f"↷ 用户跳过: {pair.filename}")
                elif requested_action == "prev":
                    # 切换到上一张，已经处理过，不需要重复计数
                    pass
                elif requested_action == "next":
                    # 切换到下一张，已经处理过，不需要重复计数
                    pass
                else:
                    # 其他失败
                    fail_count += 1
                    self.logger.error(f"✗ 处理失败: {pair.filename}")

            # 显示进度
            self._log_progress(i + 1, total_count, success_count, skip_count, fail_count)

            # 移动到下一张图像
            i += 1

        return success_count

    def _log_progress(
        self,
        current: int,
        total: int,
        success: int,
        skip: int,
        fail: int
    ) -> None:
        """记录处理进度"""
        percentage = current / total * 100
        progress_bar = self._create_progress_bar(current, total)

        self.logger.info(
            f"进度: {progress_bar} {percentage:.1f}% "
            f"(成功: {success}, 跳过: {skip}, 失败: {fail})"
        )

    def _create_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """创建进度条"""
        if total == 0:
            return "[>]"

        filled = int(width * current / total)
        bar = "[" + "=" * filled + ">" + " " * (width - filled - 1) + "]"
        return bar

    def _log_statistics(self, success_count: int) -> None:
        """输出统计信息"""
        self.end_time = time.time()
        total_time = self.end_time - self.start_time

        total_count = len(self.pairs)
        fail_count = total_count - success_count

        self.logger.info("=" * 60)
        self.logger.info("处理完成!")
        self.logger.info("=" * 60)
        self.logger.info(f"总图像对: {total_count}")
        self.logger.info(f"成功处理: {success_count}")
        self.logger.info(f"失败/跳过: {fail_count}")
        self.logger.info(f"总耗时: {total_time:.2f}秒")

        if success_count > 0:
            avg_time = total_time / success_count
            self.logger.info(f"平均每对耗时: {avg_time:.2f}秒")

        # 输出目录信息
        self.logger.info(f"输出目录结构:")
        self.logger.info(f"  - 可见光: {self.config.output_vis_dir}")
        self.logger.info(f"  - 红外: {self.config.output_ir_dir}")
        self.logger.info(f"  - 掩膜: {self.config.output_mask_dir}")

        if success_count == 0:
            self.logger.warning("未成功处理任何图像对")
        elif success_count == total_count:
            self.logger.info("所有图像对处理成功!")
        else:
            self.logger.warning(f"部分图像对处理失败: {fail_count}/{total_count}")

    def get_pairs(self) -> List[ImagePair]:
        """获取图像对列表"""
        return self.pairs.copy()

    def get_current_pair(self) -> Optional[ImagePair]:
        """获取当前图像对"""
        if 0 <= self.current_idx < len(self.pairs):
            return self.pairs[self.current_idx]
        return None

    def next_pair(self) -> bool:
        """切换到下一对图像"""
        if self.current_idx < len(self.pairs) - 1:
            self.current_idx += 1
            return True
        return False

    def prev_pair(self) -> bool:
        """切换到上一对图像"""
        if self.current_idx > 0:
            self.current_idx -= 1
            return True
        return False