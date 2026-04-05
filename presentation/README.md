# 多模态图像修复程序 - 展示页面

这是一个用于配合项目演示和演讲的现代化单页展示网站。页面展示了多模态图像修复程序的技术架构、功能特点和使用流程。

## 页面功能

### 主要内容区域
1. **首页/封面** - 项目简介和视觉化展示
2. **项目概述** - 问题定义、解决方案和核心价值
3. **技术架构** - 技术栈和系统架构图
4. **功能演示** - 使用步骤和修复效果对比
5. **技术深度** - 核心算法和工程实践
6. **项目价值** - 技术成果与个人成长

### 交互功能
- **响应式导航** - 自动适应不同屏幕尺寸
- **平滑滚动** - 点击导航项平滑跳转到对应区域
- **滚动高亮** - 自动高亮当前显示的章节
- **卡片动画** - 悬停效果和加载动画
- **代码复制** - 一键复制代码片段
- **演讲模式** - 全屏展示，支持键盘导航

## 使用方式

### 1. 直接打开
直接在浏览器中打开 `index.html` 文件即可：
```bash
# 在文件管理器中双击 index.html
# 或使用浏览器打开 file:///path/to/presentation/index.html
```

### 2. 通过Python简单HTTP服务器（推荐）
```bash
# 进入presentation目录
cd presentation

# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

然后在浏览器中访问：http://localhost:8000

### 3. 演讲模式
点击页面右下角的"演讲模式"按钮进入全屏演示模式：
- **全屏显示**：隐藏导航栏和页脚
- **键盘控制**：
  - `→` 或 `空格` 或 `PageDown`：下一节
  - `←` 或 `PageUp`：上一节
  - `ESC`：退出演讲模式
- **鼠标控制**：使用右下角的控制按钮

## 文件结构
```
presentation/
├── index.html              # 主页面
├── css/
│   └── style.css          # 样式文件
├── js/
│   └── main.js            # 交互脚本
└── README.md              # 本文件
```

## 自定义修改

### 修改内容
- **文本内容**：直接编辑 `index.html` 中的文字
- **样式**：修改 `css/style.css` 中的CSS变量和样式
- **交互**：修改 `js/main.js` 中的JavaScript代码

### 颜色主题
在 `css/style.css` 的 `:root` 部分修改CSS变量：
```css
:root {
    --primary-color: #2563eb;    /* 主色调 */
    --secondary-color: #7c3aed;  /* 辅助色 */
    --text-primary: #1f2937;     /* 主要文字颜色 */
    /* ... 其他变量 */
}
```

### 添加新章节
1. 在 `index.html` 的 `<main>` 中添加新的 `<section>`
2. 在导航菜单中添加对应的链接
3. 在CSS中添加相应的样式
4. 在JavaScript的 `sectionsOrder` 数组中添加章节ID

## 浏览器兼容性
- Chrome 60+
- Firefox 55+
- Safari 10.1+
- Edge 79+

## 注意事项
1. 页面使用现代CSS特性（CSS Grid、Flexbox、CSS变量）
2. 需要网络连接加载Font Awesome图标和Google字体
3. 演讲模式需要浏览器支持Fullscreen API
4. 复制代码功能需要浏览器支持Clipboard API

## 打印样式
页面已优化打印样式：
- 移除背景颜色和阴影
- 调整字体大小和间距
- 保持代码片段可读性

使用浏览器的打印功能（Ctrl+P）即可打印页面。

## 许可证
本展示页面为多模态图像修复项目的一部分，遵循项目相同的许可证。