#!/usr/bin/env python3
"""
LaMa修复器模块
使用LaMa模型进行图像修复，支持ModelScope和外部仓库两种模式
"""

import os
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from .base import BaseInpainter
from typing import Optional, Tuple


class LamaInpainter(BaseInpainter):
    """LaMa修复器"""

    def __init__(
        self,
        mode: str = "modelscope",
        model_id: str = "iic/cv_fft_inpainting_lama",
        use_gpu: bool = True
    ):
        """
        初始化LaMa修复器

        Args:
            mode: 运行模式 ("modelscope" 或 "external_repo")
            model_id: ModelScope模型ID（仅modelscope模式有效）
            use_gpu: 是否使用GPU（如果可用）
        """
        super().__init__(name="LamaInpainter")
        self.mode = mode.lower()
        self.model_id = model_id
        self.use_gpu = use_gpu

        # 运行时变量
        self.pipeline = None
        self.repo_path = None
        self.device = "cuda" if use_gpu else "cpu"

        self.logger.info(f"初始化LaMa修复器，模式: {mode}, 设备: {self.device}")

    def initialize(self) -> bool:
        """
        初始化LaMa修复器

        Returns:
            是否初始化成功
        """
        if self.mode == "modelscope":
            success = self._init_modelscope()
        elif self.mode == "external_repo":
            success = self._init_external_repo()
        else:
            self.logger.error(f"未知的LaMa模式: {self.mode}")
            success = False

        self._initialized = success
        if success:
            self.logger.info(f"LaMa修复器初始化成功 (模式: {self.mode})")
        else:
            self.logger.warning(f"LaMa修复器初始化失败 (模式: {self.mode})")

        return success

    def _init_modelscope(self) -> bool:
        """初始化ModelScope pipeline"""
        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks

            self.logger.info(f"加载ModelScope模型: {self.model_id}")

            # 创建修复pipeline
            self.pipeline = pipeline(
                Tasks.image_inpainting,
                model=self.model_id,
                device=self.device
            )

            # 测试pipeline是否可用
            test_image = np.zeros((64, 64, 3), dtype=np.uint8)
            test_mask = np.zeros((64, 64), dtype=np.uint8)
            test_input = {"img": test_image, "mask": test_mask}

            # 尝试运行一次测试推理（可能会失败，但可以检测pipeline状态）
            try:
                _ = self.pipeline(test_input)
            except Exception as e:
                self.logger.warning(f"测试推理失败（可能正常）: {e}")

            self.logger.info("ModelScope pipeline加载成功")
            return True

        except ImportError as e:
            self.logger.error(f"ModelScope导入失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"ModelScope初始化失败: {e}", exc_info=True)
            return False

    def _init_external_repo(self) -> bool:
        """初始化外部仓库模式"""
        # 从环境变量获取仓库路径
        self.repo_path = os.getenv("LAMA_REPO_PATH")
        if not self.repo_path:
            self.logger.error("环境变量 LAMA_REPO_PATH 未设置")
            return False

        self.repo_path = Path(self.repo_path)
        if not self.repo_path.exists():
            self.logger.error(f"LaMa仓库路径不存在: {self.repo_path}")
            return False

        # 检查推理脚本
        possible_scripts = ["inference.py", "inpaint.py", "predict.py", "demo.py"]
        self.script_path = None

        for script_name in possible_scripts:
            script_path = self.repo_path / script_name
            if script_path.exists():
                self.script_path = script_path
                break

        if self.script_path is None:
            self.logger.error(f"在LaMa仓库中未找到推理脚本: {self.repo_path}")
            return False

        self.logger.info(f"找到LaMa推理脚本: {self.script_path}")
        return True

    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        使用LaMa修复图像

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

        if not self.is_available():
            raise RuntimeError("LaMa修复器未初始化或不可用")

        try:
            if self.mode == "modelscope":
                result = self._inpaint_modelscope(image, mask)
            else:  # external_repo
                result = self._inpaint_external_repo(image, mask)

            self.logger.info("LaMa修复完成")
            return result

        except Exception as e:
            error_msg = f"LaMa修复失败: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _inpaint_modelscope(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """使用ModelScope进行修复"""
        from modelscope.outputs import OutputKeys

        # 将BGR图像转换为RGB PIL.Image
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # 将掩膜转换为PIL.Image（单通道）
        pil_mask = Image.fromarray(mask)

        # 准备输入
        inp = {"img": pil_image, "mask": pil_mask}

        # 记录处理信息
        mask_pixels = np.sum(mask > 0)
        self.logger.info(f"开始LaMa修复 (ModelScope)，修复区域: {mask_pixels}像素")

        # 执行修复
        result = self.pipeline(inp)

        # 提取输出图像
        output_img = result[OutputKeys.OUTPUT_IMG]

        # 如果输出是PIL.Image，转换为numpy数组
        if isinstance(output_img, Image.Image):
            output_img = np.array(output_img)
            # PIL.Image是RGB，转换为BGR
            output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)

        # 确保输出为uint8 BGR格式
        if output_img.dtype != np.uint8:
            output_img = (np.clip(output_img, 0, 1) * 255).astype(np.uint8)

        return output_img

    def _inpaint_external_repo(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """使用外部仓库进行修复"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_img, \
             tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_mask:

            img_path = f_img.name
            mask_path = f_mask.name

            # 保存临时文件
            cv2.imwrite(img_path, image)
            cv2.imwrite(mask_path, mask)

            # 准备输出路径
            output_path = img_path + "_output.png"

            # 构建命令
            cmd = [
                "python", str(self.script_path),
                "--image", img_path,
                "--mask", mask_path,
                "--output", output_path
            ]

            # 添加GPU参数（如果可用）
            if self.use_gpu:
                cmd.append("--device")
                cmd.append("cuda")

            self.logger.info(f"执行外部命令: {' '.join(cmd)}")

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            # 检查结果
            if result.returncode != 0:
                error_msg = f"外部LaMa失败: {result.stderr}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            # 读取结果图像
            if not os.path.exists(output_path):
                error_msg = f"输出文件未生成: {output_path}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            result_img = cv2.imread(output_path)
            if result_img is None:
                error_msg = f"无法读取输出图像: {output_path}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            # 清理临时文件
            try:
                os.unlink(img_path)
                os.unlink(mask_path)
                os.unlink(output_path)
            except Exception as e:
                self.logger.warning(f"清理临时文件失败: {e}")

            return result_img

    def is_available(self) -> bool:
        """检查修复器是否可用"""
        if self.mode == "modelscope":
            return self.pipeline is not None
        else:  # external_repo
            return self.script_path is not None and self.script_path.exists()

    def get_mode(self) -> str:
        """获取当前运行模式"""
        return self.mode

    def get_model_info(self) -> dict:
        """获取模型信息"""
        info = {
            "mode": self.mode,
            "device": self.device,
            "available": self.is_available()
        }

        if self.mode == "modelscope":
            info["model_id"] = self.model_id
            info["pipeline_loaded"] = self.pipeline is not None
        else:
            info["repo_path"] = str(self.repo_path) if self.repo_path else None
            info["script_path"] = str(self.script_path) if self.script_path else None

        return info