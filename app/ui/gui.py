#!/usr/bin/env python3
"""
GUI界面模块
提供图形界面选择路径并启动多模态图像修复程序
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import queue
import sys
from pathlib import Path
import os


class InpaintingGUI:
    """多模态图像修复程序GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("多模态图像修复程序")
        self.root.geometry("800x600")

        # 设置图标（如果有）
        # self.root.iconbitmap(default='icon.ico')

        # 创建队列用于线程间通信
        self.output_queue = queue.Queue()

        # 创建UI组件
        self.create_widgets()

        # 启动队列处理器
        self.process_queue()

        # 设置关闭窗口事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 存储子进程引用
        self.process = None

    def create_widgets(self):
        """创建UI组件"""

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="多模态图像修复程序 (VIS + IR)",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 可见光图像目录
        ttk.Label(main_frame, text="可见光图像目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.vis_dir_var = tk.StringVar()
        vis_entry = ttk.Entry(main_frame, textvariable=self.vis_dir_var, width=50)
        vis_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_vis_dir).grid(row=1, column=2, padx=5, pady=5)

        # 红外图像目录
        ttk.Label(main_frame, text="红外图像目录:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ir_dir_var = tk.StringVar()
        ir_entry = ttk.Entry(main_frame, textvariable=self.ir_dir_var, width=50)
        ir_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_ir_dir).grid(row=2, column=2, padx=5, pady=5)

        # 输出目录
        ttk.Label(main_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.out_dir_var = tk.StringVar()
        out_entry = ttk.Entry(main_frame, textvariable=self.out_dir_var, width=50)
        out_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_out_dir).grid(row=3, column=2, padx=5, pady=5)

        # 高级选项框架（可折叠）
        self.advanced_frame = ttk.LabelFrame(main_frame, text="高级选项", padding="10")
        self.advanced_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        self.advanced_frame.columnconfigure(1, weight=1)

        # 修复后端选择
        ttk.Label(self.advanced_frame, text="修复后端:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.backend_var = tk.StringVar(value="opencv")
        backend_combo = ttk.Combobox(
            self.advanced_frame,
            textvariable=self.backend_var,
            values=["opencv", "lama"],
            state="readonly",
            width=20
        )
        backend_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # LaMa模式选择（仅当后端为lama时启用）
        ttk.Label(self.advanced_frame, text="LaMa模式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.lama_mode_var = tk.StringVar(value="modelscope")
        self.lama_mode_combo = ttk.Combobox(
            self.advanced_frame,
            textvariable=self.lama_mode_var,
            values=["modelscope", "external_repo"],
            state="readonly",
            width=20
        )
        self.lama_mode_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 画笔半径
        ttk.Label(self.advanced_frame, text="画笔半径:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.brush_radius_var = tk.StringVar(value="20")
        brush_spinbox = ttk.Spinbox(
            self.advanced_frame,
            textvariable=self.brush_radius_var,
            from_=1,
            to=100,
            width=10
        )
        brush_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # 绑定后端选择事件以更新LaMa模式状态
        backend_combo.bind("<<ComboboxSelected>>", self.on_backend_changed)
        self.on_backend_changed(None)  # 初始化状态

        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.run_button = ttk.Button(
            button_frame,
            text="开始修复",
            command=self.start_inpainting,
            width=15
        )
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop_inpainting,
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="清除日志",
            command=self.clear_log,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # 日志输出区域
        ttk.Label(main_frame, text="程序输出:").grid(row=6, column=0, sticky=tk.W, pady=(10, 0))

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # 滚动文本框用于显示日志
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 10)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

    def browse_vis_dir(self):
        """浏览可见光图像目录"""
        dir_path = filedialog.askdirectory(title="选择可见光图像目录")
        if dir_path:
            self.vis_dir_var.set(dir_path)

    def browse_ir_dir(self):
        """浏览红外图像目录"""
        dir_path = filedialog.askdirectory(title="选择红外图像目录")
        if dir_path:
            self.ir_dir_var.set(dir_path)

    def browse_out_dir(self):
        """浏览输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.out_dir_var.set(dir_path)

    def on_backend_changed(self, event):
        """修复后端选择改变事件"""
        if self.backend_var.get() == "lama":
            self.lama_mode_combo.config(state="readonly")
        else:
            self.lama_mode_combo.config(state=tk.DISABLED)

    def start_inpainting(self):
        """开始图像修复处理"""
        # 验证输入
        vis_dir = self.vis_dir_var.get().strip()
        ir_dir = self.ir_dir_var.get().strip()
        out_dir = self.out_dir_var.get().strip()

        if not vis_dir:
            self.log_message("错误: 请选择可见光图像目录", "error")
            return

        if not ir_dir:
            self.log_message("错误: 请选择红外图像目录", "error")
            return

        if not out_dir:
            self.log_message("错误: 请选择输出目录", "error")
            return

        # 检查目录是否存在
        if not os.path.exists(vis_dir):
            self.log_message(f"错误: 可见光目录不存在: {vis_dir}", "error")
            return

        if not os.path.exists(ir_dir):
            self.log_message(f"错误: 红外目录不存在: {ir_dir}", "error")
            return

        # 创建输出目录（如果不存在）
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            self.log_message(f"错误: 无法创建输出目录: {e}", "error")
            return

        # 构建命令行参数
        cmd = [
            sys.executable,
            "run.py",
            "--vis-dir", vis_dir,
            "--ir-dir", ir_dir,
            "--out-dir", out_dir,
            "--backend", self.backend_var.get(),
            "--brush-radius", self.brush_radius_var.get()
        ]

        # 添加LaMa特定参数
        if self.backend_var.get() == "lama":
            cmd.extend(["--lama-mode", self.lama_mode_var.get()])

        # 显示命令
        self.log_message(f"执行命令: {' '.join(cmd)}", "info")
        self.log_message("-" * 60, "info")

        # 更新UI状态
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("正在运行...")

        # 在工作目录中运行（项目根目录）
        project_root = Path(__file__).parent.parent.parent

        # 启动子进程
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )

            # 启动线程读取输出
            self.reader_thread = threading.Thread(
                target=self.read_process_output,
                args=(self.process,),
                daemon=True
            )
            self.reader_thread.start()

        except Exception as e:
            self.log_message(f"错误: 启动进程失败: {e}", "error")
            self.reset_ui_state()

    def read_process_output(self, process):
        """读取子进程输出"""
        for line in iter(process.stdout.readline, ''):
            # 将输出放入队列，由主线程处理
            self.output_queue.put(line)

        # 进程结束
        process.stdout.close()
        return_code = process.wait()
        self.output_queue.put(f"PROCESS_EXIT:{return_code}")

    def process_queue(self):
        """处理输出队列（在主线程中）"""
        try:
            while True:
                # 非阻塞获取队列中的项目
                try:
                    item = self.output_queue.get_nowait()
                except queue.Empty:
                    break

                # 处理项目
                if item.startswith("PROCESS_EXIT:"):
                    # 进程退出
                    return_code = int(item.split(":")[1])
                    self.on_process_exit(return_code)
                else:
                    # 普通输出
                    self.log_message(item.rstrip(), "output")

        finally:
            # 每100毫秒再次检查队列
            self.root.after(100, self.process_queue)

    def on_process_exit(self, return_code):
        """进程退出处理"""
        self.process = None

        if return_code == 0:
            self.log_message("-" * 60, "info")
            self.log_message("处理完成！", "success")
            self.status_var.set("处理完成")
        elif return_code == 130:
            self.log_message("-" * 60, "info")
            self.log_message("处理被用户中断", "warning")
            self.status_var.set("用户中断")
        else:
            self.log_message("-" * 60, "info")
            self.log_message(f"处理失败，退出代码: {return_code}", "error")
            self.status_var.set("处理失败")

        # 重置UI状态
        self.reset_ui_state()

    def stop_inpainting(self):
        """停止当前处理"""
        if self.process and self.process.poll() is None:
            self.log_message("正在停止处理...", "warning")
            self.process.terminate()
            self.status_var.set("正在停止...")

    def reset_ui_state(self):
        """重置UI状态"""
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def log_message(self, message, msg_type="info"):
        """在日志区域显示消息"""
        # 获取当前时间
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据消息类型设置颜色
        if msg_type == "error":
            tag = "error"
            prefix = f"[{timestamp}] ERROR: "
        elif msg_type == "warning":
            tag = "warning"
            prefix = f"[{timestamp}] WARNING: "
        elif msg_type == "success":
            tag = "success"
            prefix = f"[{timestamp}] SUCCESS: "
        elif msg_type == "output":
            tag = "output"
            prefix = f"[{timestamp}] "
        else:
            tag = "info"
            prefix = f"[{timestamp}] INFO: "

        # 插入消息
        self.log_text.insert(tk.END, prefix + message + "\n", tag)

        # 滚动到最后
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()

    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("就绪")

    def on_closing(self):
        """窗口关闭事件处理"""
        if self.process and self.process.poll() is None:
            if tk.messagebox.askokcancel("退出", "处理正在进行中，确定要退出吗？"):
                self.process.terminate()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """GUI主函数"""
    root = tk.Tk()

    # 配置标签样式
    style = ttk.Style()
    style.configure("Error.TLabel", foreground="red")
    style.configure("Success.TLabel", foreground="green")

    # 创建GUI
    app = InpaintingGUI(root)

    # 配置文本标签
    app.log_text.tag_config("error", foreground="red")
    app.log_text.tag_config("warning", foreground="orange")
    app.log_text.tag_config("success", foreground="green")
    app.log_text.tag_config("info", foreground="blue")
    app.log_text.tag_config("output", foreground="black")

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()