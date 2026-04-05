# 多模态图像修复程序 (Multimodal Image Inpainting)

一个基于Python的桌面交互式图像修复程序，专门用于处理可见光(VIS)和红外(IR)图像对。用户可以在可见光图像上绘制掩膜，程序会自动将同一掩膜应用于对应的红外图像，然后使用LaMa或OpenCV修复功能对两张图像进行独立修复。

## 功能特性

- **多模态支持**: 同时处理可见光(VIS)和红外(IR)图像对
- **交互式掩膜编辑**: 在可见光图像上使用鼠标绘制修复区域
- **双修复后端**: 支持OpenCV（快速调试）和LaMa（高质量修复）
- **批量处理**: 支持连续处理多个图像对
- **完整日志**: 详细的处理日志和错误报告
- **模块化设计**: 易于扩展和维护的代码结构

## 目录结构

```
multimodal_inpainting/
├─ app/                          # 应用程序代码
│  ├─ __init__.py
│  ├─ main.py                    # 主程序入口
│  ├─ config.py                  # 配置管理
│  ├─ logger.py                  # 日志配置
│  ├─ utils/                     # 工具模块
│  │  ├─ __init__.py
│  │  ├─ io.py                   # 文件I/O操作
│  │  ├─ image.py                # 图像处理工具
│  │  └─ file_matcher.py         # 图像配对
│  ├─ ui/                        # 用户界面
│  │  ├─ __init__.py
│  │  └─ mask_editor.py          # OpenCV交互编辑器
│  ├─ core/                      # 核心处理
│  │  ├─ __init__.py
│  │  ├─ pipeline.py             # 批处理流程
│  │  └─ processor.py            # 单图像对处理
│  └─ inpainters/                # 修复器模块
│     ├─ __init__.py
│     ├─ base.py                 # 抽象接口
│     ├─ opencv_inpainter.py     # OpenCV修复器
│     └─ lama_inpainter.py       # LaMa修复器
├─ dataset/                      # 示例数据目录
│  ├─ visible/                   # 可见光图像
│  └─ infrared/                  # 红外图像
├─ output/                       # 输出目录
│  ├─ visible/                   # 修复后的可见光图像
│  ├─ infrared/                  # 修复后的红外图像
│  └─ masks/                     # 使用的掩膜
├─ requirements.txt              # Python依赖包
├─ README.md                     # 本文件
└─ run.py                        # 启动脚本
```

## 环境要求

- Python 3.10 或更高版本
- OpenCV 4.8.0 或更高版本
- PyTorch 2.0.0 或更高版本（LaMa修复需要）
- ModelScope 1.9.0 或更高版本（LaMa修复需要）

## 快速开始

### 启动方式选择
本程序提供两种启动方式：
- **命令行模式**：适合批量处理和自动化脚本
- **图形界面(GUI)模式**：适合交互式使用，提供友好的路径选择界面

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备数据

将图像文件按以下方式组织：

```
dataset/
├─ visible/     # 可见光图像目录
│  ├─ image1.jpg
│  ├─ image2.png
│  └─ ...
└─ infrared/    # 红外图像目录
   ├─ image1.jpg    # 与visible/image1.jpg对应
   ├─ image2.png    # 与visible/image2.png对应
   └─ ...
```

**重要**: 可见光和红外图像必须**文件名相同**，且**分辨率相同**。

### 3. 运行程序

#### 使用OpenCV后端（调试模式）

```bash
python run.py \
  --vis-dir dataset/visible \
  --ir-dir dataset/infrared \
  --out-dir output \
  --backend opencv \
  --brush-radius 20
```

#### 使用LaMa后端（ModelScope模式）

```bash
python run.py \
  --vis-dir dataset/visible \
  --ir-dir dataset/infrared \
  --out-dir output \
  --backend lama \
  --lama-mode modelscope \
  --brush-radius 20
```

#### 使用LaMa后端（外部仓库模式）

```bash
# 设置环境变量
export LAMA_REPO_PATH=/path/to/your/lama-repo  # Linux/Mac
# 或
set LAMA_REPO_PATH=C:\path\to\your\lama-repo   # Windows

# 运行程序
python run.py \
  --vis-dir dataset/visible \
  --ir-dir dataset/infrared \
  --out-dir output \
  --backend lama \
  --lama-mode external_repo \
  --brush-radius 20
```

## 图形界面(GUI)启动

如果您偏好使用图形界面，可以使用GUI版本的程序：

### 启动GUI
```bash
python gui_run.py
```

### GUI界面功能
1. **目录选择**：
   - 通过浏览按钮选择可见光图像目录
   - 通过浏览按钮选择红外图像目录
   - 通过浏览按钮选择输出目录

2. **高级选项**：
   - 修复后端选择：OpenCV 或 LaMa
   - LaMa模式选择（仅当使用LaMa后端时）
   - 画笔半径设置

3. **运行控制**：
   - 开始修复：启动处理流程
   - 停止：终止正在运行的处理
   - 清除日志：清空输出窗口

4. **实时日志**：
   - 显示程序运行状态和输出
   - 彩色编码的消息类型（信息、警告、错误、成功）
   - 自动滚动到最新消息

### GUI工作流程
1. 启动 `python gui_run.py`
2. 选择三个目录路径
3. 配置高级选项（可选）
4. 点击"开始修复"按钮
5. 程序会在后台运行，打开OpenCV窗口供您交互式绘制掩膜
6. 在GUI中查看实时日志输出
7. 处理完成后查看输出目录中的结果

## 命令行参数

### 必需参数
- `--vis-dir`: 可见光图像目录
- `--ir-dir`: 红外图像目录
- `--out-dir`: 输出目录

### 修复后端参数
- `--backend`: 修复后端，可选 `opencv` 或 `lama`（默认: `opencv`）
- `--lama-mode`: LaMa运行模式，可选 `modelscope` 或 `external_repo`（默认: `modelscope`）
- `--lama-model-id`: ModelScope模型ID（默认: `iic/cv_fft_inpainting_lama`）

### UI参数
- `--brush-radius`: 画笔半径（默认: 20）
- `--max-display-width`: 最大显示宽度（默认: 1024）
- `--max-display-height`: 最大显示高度（默认: 768）

### 其他参数
- `--log-level`: 日志级别，可选 `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`（默认: `INFO`）
- `--log-file`: 日志文件路径（可选）

## 掩膜编辑器使用说明

程序启动后，会打开一个OpenCV窗口显示可见光图像。您可以在图像上绘制掩膜：

### 鼠标操作
- **左键拖动**: 绘制掩膜区域
- **鼠标滚轮**: 调整画笔大小

### 键盘快捷键
- `u`: 撤销上一步操作
- `c`: 清空所有绘制
- `+`/`=`: 增大画笔大小
- `-`: 减小画笔大小
- `Enter`: 确认掩膜并开始修复
- `n`: 跳过当前图像
- `q`/`Esc`: 退出程序

### 显示信息
窗口顶部显示：
- 当前文件名
- 画笔大小
- 掩膜区域统计
- 快捷键提示

## LaMa修复器配置

### ModelScope模式（推荐）
程序会自动从ModelScope下载并加载LaMa模型。首次运行可能需要较长时间下载模型文件。

### 外部仓库模式
如果您有本地的LaMa仓库，可以通过环境变量`LAMA_REPO_PATH`指定路径。仓库中需要包含推理脚本（如`inference.py`、`inpaint.py`等）。

## 输出文件

处理完成后，输出目录结构如下：

```
output/
├─ visible/           # 修复后的可见光图像
│  ├─ image1.jpg
│  ├─ image2.png
│  └─ ...
├─ infrared/          # 修复后的红外图像
│  ├─ image1.jpg
│  ├─ image2.png
│  └─ ...
└─ masks/             # 使用的掩膜
   ├─ image1_mask.png
   ├─ image2_mask.png
   └─ ...
```

## 错误处理

### 常见问题

1. **图像加载失败**
   - 检查文件路径和权限
   - 确认图像格式支持（PNG、JPG、JPEG、BMP、TIFF）

2. **尺寸不匹配**
   - 确保可见光和红外图像分辨率相同
   - 使用图像编辑工具调整尺寸

3. **LaMa初始化失败**
   - 检查网络连接（ModelScope模式）
   - 确认ModelScope已正确安装
   - 检查环境变量`LAMA_REPO_PATH`（外部仓库模式）

4. **修复过程失败**
   - 检查GPU内存是否充足（LaMa模式）
   - 尝试减小画笔大小或修复区域
   - 使用OpenCV后端作为回退

### 日志文件

程序会输出详细的日志信息，包括：
- 处理进度和状态
- 错误和警告信息
- 性能统计
- 用户操作记录

## 开发指南

### 添加新的修复器

1. 在`app/inpainters/`目录中创建新的修复器类
2. 继承`BaseInpainter`基类
3. 实现`initialize()`和`inpaint()`方法
4. 在`app/main.py`的`create_inpainter()`函数中添加支持

### 扩展UI功能

1. 修改`app/ui/mask_editor.py`
2. 添加新的鼠标或键盘事件处理
3. 更新显示界面

### 添加新的图像格式支持

1. 修改`app/utils/image.py`中的`load_image()`方法
2. 更新`app/utils/file_matcher.py`中的`SUPPORTED_EXTS`列表

## 性能优化

### 内存使用
- 大图像会自动缩放到适合显示的大小
- 修复完成后及时释放内存
- 支持批处理模式，避免重复加载模型

### GPU加速
- LaMa修复器支持GPU加速
- 自动检测CUDA可用性
- 可通过`--use-gpu`参数控制

### 多线程处理
- 图像加载和保存使用异步IO
- 修复过程支持并行处理（未来版本）

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 贡献指南

欢迎提交Issue和Pull Request！请确保：
1. 代码符合PEP 8规范
2. 添加适当的测试用例
3. 更新相关文档
4. 通过基本的代码检查

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送电子邮件至开发者

## 致谢

- LaMa模型作者
- OpenCV和PyTorch社区
- ModelScope平台
- 所有贡献者和用户