#!/usr/bin/env python3
"""
多模态图像修复程序启动脚本
"""

import sys
from pathlib import Path

# 添加app目录到Python路径
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# 导入并运行主程序
from app.main import main

if __name__ == "__main__":
    sys.exit(main())