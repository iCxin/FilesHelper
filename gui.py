import os
import shutil
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import queue
import webbrowser
from datetime import datetime, timedelta
import logging
from logging.handlers import TimedRotatingFileHandler

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("文件整理助手")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5, font=('微软雅黑', 9))
        self.style.configure("TLabel", font=('微软雅黑', 9))
        self.style.configure("TEntry", font=('微软雅黑', 9))
        self.style.configure("Header.TLabel", font=('微软雅黑', 12, 'bold'))
        self.style.configure("Title.TLabel", font=('微软雅黑', 16, 'bold'))
        self.style.configure("Subtitle.TLabel", font=('微软雅黑', 10))
        self.style.configure("Link.TLabel", font=('微软雅黑', 9, 'underline'), foreground='blue')
        
        # 设置主题色
        self.style.configure("Accent.TButton", background="#4a86e8", foreground="white")
        self.style.configure("Accent.TFrame", background="#f0f0f0")
        self.style.configure("Black.TButton", foreground="black")  # 添加黑色文字按钮样式
        
        # 初始化变量
        self.rules = {}
        self.resources_dir = Path("resources")
        self.resources_dir.mkdir(exist_ok=True)
        self.config_file = self.resources_dir / "file_rules.json"
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0
        self.is_processing = False
        self.log_queue = queue.Queue()
        self.log_retention_days = 7  # 默认日志保留7天
        
        # 创建日志目录
        self.log_dir = self.resources_dir / "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 设置日志
        self.setup_logging()
        
        # 加载规则和窗口位置
        self.load_rules()
        self.load_window_position()
        self.load_log_settings()
        
        # 创建界面
        self.create_widgets()
        
        # 启动日志更新线程
        self.update_log_thread = threading.Thread(target=self.update_log, daemon=True)
        self.update_log_thread.start()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_logging(self):
        """设置日志系统"""
        log_file = os.path.join(self.log_dir, "file_organizer.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 创建按天轮转的文件处理器
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=self.log_retention_days,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 清除现有的处理器，避免重复
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        logger.addHandler(file_handler)
        
        # 清理旧日志
        self.cleanup_old_logs()
        
        # 记录启动日志
        logging.info("程序启动")
        logging.info(f"当前日志保留天数: {self.log_retention_days} 天")
    
    def cleanup_old_logs(self):
        """清理超过保留天数的日志文件"""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).days > self.log_retention_days:
                        os.remove(file_path)
        except Exception as e:
            logging.error(f"清理日志文件时出错: {str(e)}")
    
    def load_log_settings(self):
        """加载日志设置"""
        try:
            settings_file = self.resources_dir / "log_settings.json"
            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.log_retention_days = settings.get("retention_days", 7)
        except Exception as e:
            logging.error(f"加载日志设置时出错: {str(e)}")
    
    def save_log_settings(self):
        """保存日志设置"""
        try:
            settings = {
                "retention_days": self.log_retention_days
            }
            settings_file = self.resources_dir / "log_settings.json"
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存日志设置时出错: {str(e)}")
    
    def show_log_settings_dialog(self):
        """显示日志设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("日志设置")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使对话框居中显示
        self.center_window(dialog)
        
        # 日志保留天数设置
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="日志保留天数:").pack(anchor=tk.W)
        
        days_var = tk.StringVar(value=str(self.log_retention_days))
        days_entry = ttk.Entry(frame, textvariable=days_var, width=10)
        days_entry.pack(anchor=tk.W, pady=5)
        
        def save_settings():
            try:
                days = int(days_var.get())
                if days < 1:
                    messagebox.showwarning("警告", "保留天数必须大于0！", parent=dialog)
                    return
                
                self.log_retention_days = days
                self.save_log_settings()
                self.setup_logging()  # 重新设置日志系统
                dialog.destroy()
                
                # 添加日志
                self.add_log(f"已更新日志保留天数为 {days} 天")
            except ValueError:
                messagebox.showwarning("警告", "请输入有效的数字！", parent=dialog)
        
        # 按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="保存", command=save_settings, style="Black.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, style="Black.TButton").pack(side=tk.RIGHT)
    
    def load_rules(self):
        """加载已保存的分类规则"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
            except json.JSONDecodeError:
                messagebox.showwarning("警告", "规则文件损坏，将创建新的规则文件")
                self.rules = {}
        else:
            self.rules = {}
    
    def save_rules(self):
        """保存分类规则"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"保存规则时出错: {str(e)}")
    
    def load_window_position(self):
        """加载窗口位置"""
        try:
            position_file = self.resources_dir / "window_position.json"
            if position_file.exists():
                with open(position_file, "r", encoding="utf-8") as f:
                    position = json.load(f)
                    self.root.geometry(position["geometry"])
        except Exception as e:
            logging.error(f"加载窗口位置时出错: {str(e)}")
    
    def save_window_position(self):
        """保存窗口位置"""
        try:
            position = {
                "geometry": self.root.geometry()
            }
            position_file = self.resources_dir / "window_position.json"
            with open(position_file, "w", encoding="utf-8") as f:
                json.dump(position, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存窗口位置时出错: {str(e)}")
    
    def center_window(self, window):
        """使窗口居中显示"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        # 记录关闭日志
        logging.info("程序关闭")
        self.save_window_position()
        self.root.destroy()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="文件整理助手", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="文件分类工具", style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(5, 0))
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 规则管理选项卡
        rules_frame = ttk.Frame(notebook, padding="10")
        notebook.add(rules_frame, text="规则管理")
        
        # 文件整理选项卡
        organize_frame = ttk.Frame(notebook, padding="10")
        notebook.add(organize_frame, text="文件整理")
        
        # 日志选项卡
        log_frame = ttk.Frame(notebook, padding="10")
        notebook.add(log_frame, text="操作日志")
        
        # 关于选项卡
        about_frame = ttk.Frame(notebook, padding="10")
        notebook.add(about_frame, text="关于")
        
        # 设置规则管理选项卡
        self.setup_rules_tab(rules_frame)
        
        # 设置文件整理选项卡
        self.setup_organize_tab(organize_frame)
        
        # 设置日志选项卡
        self.setup_log_tab(log_frame)
        
        # 设置关于选项卡
        self.setup_about_tab(about_frame)
    
    def setup_rules_tab(self, parent):
        """设置规则管理选项卡"""
        # 规则列表框架
        list_frame = ttk.LabelFrame(parent, text="当前规则", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 规则列表
        self.rules_tree = ttk.Treeview(list_frame, columns=("keyword", "folder"), show="headings")
        self.rules_tree.heading("keyword", text="关键词/扩展名")
        self.rules_tree.heading("folder", text="目标文件夹")
        self.rules_tree.column("keyword", width=200)
        self.rules_tree.column("folder", width=200)
        self.rules_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加规则按钮 - 使用黑色文字样式
        add_btn = ttk.Button(btn_frame, text="添加规则", command=self.show_add_rule_dialog, style="Black.TButton")
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除规则按钮
        delete_btn = ttk.Button(btn_frame, text="删除规则", command=self.delete_rule)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入规则包按钮
        import_btn = ttk.Button(btn_frame, text="导入规则包", command=self.import_rule_package)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出规则包按钮
        export_btn = ttk.Button(btn_frame, text="导出规则包", command=self.export_rule_package)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新规则列表
        self.refresh_rules_list()
    
    def setup_organize_tab(self, parent):
        """设置文件整理选项卡"""
        # 源目录框架
        source_frame = ttk.LabelFrame(parent, text="源目录", padding="10")
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_btn = ttk.Button(source_frame, text="浏览...", command=self.browse_source)
        source_btn.pack(side=tk.RIGHT)
        
        # 目标目录框架
        target_frame = ttk.LabelFrame(parent, text="目标目录", padding="10")
        target_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.target_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.target_var, width=50)
        target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        target_btn = ttk.Button(target_frame, text="浏览...", command=self.browse_target)
        target_btn.pack(side=tk.RIGHT)
        
        # 操作模式框架
        mode_frame = ttk.LabelFrame(parent, text="操作模式", padding="10")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="copy")
        copy_radio = ttk.Radiobutton(mode_frame, text="复制文件（保留源文件）", variable=self.mode_var, value="copy")
        copy_radio.pack(anchor=tk.W, pady=2)
        
        move_radio = ttk.Radiobutton(mode_frame, text="移动文件（删除源文件）", variable=self.mode_var, value="move")
        move_radio.pack(anchor=tk.W, pady=2)
        
        # 开始按钮
        start_frame = ttk.Frame(parent)
        start_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_btn = ttk.Button(start_frame, text="开始整理", command=self.start_organize, style="Black.TButton")
        self.start_btn.pack(side=tk.RIGHT)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, length=300, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(parent, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, padx=5)
    
    def setup_log_tab(self, parent):
        """设置日志选项卡"""
        # 日志框架
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保存日志按钮
        save_btn = ttk.Button(btn_frame, text="保存日志", command=self.save_log)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 清除日志按钮
        clear_btn = ttk.Button(btn_frame, text="清除日志", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 日志设置按钮
        settings_btn = ttk.Button(btn_frame, text="日志设置", command=self.show_log_settings_dialog)
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加初始日志
        self.add_log("程序启动")
        self.add_log(f"当前日志保留天数: {self.log_retention_days} 天")
    
    def setup_about_tab(self, parent):
        """设置关于选项卡"""
        # 关于信息框架
        about_frame = ttk.Frame(parent)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 应用信息
        app_info_frame = ttk.LabelFrame(about_frame, text="应用信息", padding="15")
        app_info_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(app_info_frame, text="文件整理助手", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(app_info_frame, text="版本: 1.4.0", style="Subtitle.TLabel").pack(anchor=tk.W)
        ttk.Label(app_info_frame, text="一个固定规则的文件分类工具，可以根据文件名中的关键词或文件类型自动将文件分类到不同的文件夹中。").pack(anchor=tk.W, pady=(5, 0))
        
        # 开发者信息
        dev_info_frame = ttk.LabelFrame(about_frame, text="开发者信息", padding="15")
        dev_info_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(dev_info_frame, text="开发者: cxin", style="Subtitle.TLabel").pack(anchor=tk.W)
        
        # 邮箱链接
        email_frame = ttk.Frame(dev_info_frame)
        email_frame.pack(fill=tk.X, pady=2)
        ttk.Label(email_frame, text="邮箱: ").pack(side=tk.LEFT)
        email_link = ttk.Label(email_frame, text="tojx@qq.com", style="Link.TLabel", cursor="hand2")
        email_link.pack(side=tk.LEFT)
        email_link.bind("<Button-1>", lambda e: webbrowser.open("mailto:tojx@qq.com"))
        
        # 网站链接
        website_frame = ttk.Frame(dev_info_frame)
        website_frame.pack(fill=tk.X, pady=2)
        ttk.Label(website_frame, text="个人网站: ").pack(side=tk.LEFT)
        website_link = ttk.Label(website_frame, text="www.cxin.net", style="Link.TLabel", cursor="hand2")
        website_link.pack(side=tk.LEFT)
        website_link.bind("<Button-1>", lambda e: webbrowser.open("http://www.cxin.net"))
        
        # 版权信息
        copyright_frame = ttk.Frame(about_frame)
        copyright_frame.pack(fill=tk.X, pady=10)
        ttk.Label(copyright_frame, text="© 2025 cxin. 保留所有权利。").pack(anchor=tk.CENTER)
    
    def refresh_rules_list(self):
        """刷新规则列表"""
        # 清空列表
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # 添加规则
        for keyword, folder in self.rules.items():
            self.rules_tree.insert("", tk.END, values=(keyword, folder))
    
    def show_add_rule_dialog(self):
        """显示添加规则对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加规则")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使对话框居中显示
        self.center_window(dialog)
        
        # 关键词框架
        keyword_frame = ttk.Frame(dialog, padding="10")
        keyword_frame.pack(fill=tk.X)
        
        ttk.Label(keyword_frame, text="关键词或文件扩展名:").pack(anchor=tk.W)
        keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(keyword_frame, textvariable=keyword_var, width=40)
        keyword_entry.pack(fill=tk.X, pady=5)
        
        # 文件夹框架
        folder_frame = ttk.Frame(dialog, padding="10")
        folder_frame.pack(fill=tk.X)
        
        ttk.Label(folder_frame, text="目标文件夹名称 (留空则使用关键词):").pack(anchor=tk.W)
        folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=40)
        folder_entry.pack(fill=tk.X, pady=5)
        
        # 按钮框架
        btn_frame = ttk.Frame(dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        def add_rule():
            keyword = keyword_var.get().strip()
            folder = folder_var.get().strip()
            
            if not keyword:
                messagebox.showwarning("警告", "关键词不能为空！", parent=dialog)
                return
            
            # 如果文件夹名称为空，则使用关键词作为文件夹名称
            if not folder:
                folder = keyword
            
            # 规范化文件夹名称
            folder = folder.replace('/', '_').replace('\\', '_')
            
            # 添加规则
            self.rules[keyword] = folder
            self.save_rules()
            self.refresh_rules_list()
            
            # 关闭对话框
            dialog.destroy()
            
            # 添加日志
            self.add_log(f"已添加规则: {keyword} -> {folder}")
        
        # 修改按钮样式，确保文字清晰可见
        ttk.Button(btn_frame, text="添加", command=add_rule, style="Black.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, style="Black.TButton").pack(side=tk.RIGHT)
    
    def delete_rule(self):
        """删除选中的规则"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的规则")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的规则吗？"):
            for item in selected:
                values = self.rules_tree.item(item, "values")
                keyword = values[0]
                del self.rules[keyword]
                self.add_log(f"已删除规则: {keyword}")
            
            self.save_rules()
            self.refresh_rules_list()
    
    def browse_source(self):
        """浏览源目录"""
        directory = filedialog.askdirectory(title="选择源目录")
        if directory:
            self.source_var.set(directory)
    
    def browse_target(self):
        """浏览目标目录"""
        directory = filedialog.askdirectory(title="选择目标目录")
        if directory:
            self.target_var.set(directory)
    
    def start_organize(self):
        """开始整理文件"""
        # 检查源目录和目标目录
        source_dir = self.source_var.get().strip()
        target_dir = self.target_var.get().strip()
        
        if not source_dir:
            messagebox.showwarning("警告", "请选择源目录")
            return
        
        if not target_dir:
            messagebox.showwarning("警告", "请选择目标目录")
            return
        
        # 检查源目录和目标目录是否相同
        if os.path.abspath(source_dir) == os.path.abspath(target_dir):
            messagebox.showwarning("警告", "源目录和目标目录不能相同")
            return
        
        # 检查是否有规则
        if not self.rules:
            messagebox.showwarning("警告", "请先添加分类规则")
            return
        
        # 禁用开始按钮
        self.start_btn.config(state=tk.DISABLED)
        
        # 重置进度条
        self.progress_var.set(0)
        
        # 开始处理
        self.is_processing = True
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0
        
        # 启动处理线程
        thread = threading.Thread(target=self.organize_files_thread, args=(source_dir, target_dir))
        thread.daemon = True
        thread.start()
    
    def organize_files_thread(self, source_dir, target_dir):
        """文件整理线程"""
        try:
            source_path = Path(source_dir)
            target_path = Path(target_dir)
            
            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 获取所有文件（包括子目录）
            files = list(source_path.glob('**/*'))
            total_files = sum(1 for f in files if f.is_file())
            
            if total_files == 0:
                self.add_log(f"在 {source_dir} 中没有找到任何文件")
                self.status_var.set("完成")
                self.start_btn.config(state=tk.NORMAL)
                self.is_processing = False
                return
            
            self.add_log(f"找到 {total_files} 个文件需要处理")
            self.status_var.set("正在处理...")
            
            # 处理文件
            for i, file_path in enumerate(files):
                if not self.is_processing:
                    break
                
                if file_path.is_file():
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self.progress_var.set(progress)
                    
                    # 获取文件名和扩展名
                    file_name = file_path.name.lower()
                    file_ext = file_path.suffix.lower()
                    
                    # 跳过隐藏文件
                    if file_name.startswith('.'):
                        self.skipped_files += 1
                        continue
                    
                    # 检查是否匹配任何规则
                    matched = False
                    for keyword, folder_name in self.rules.items():
                        if keyword.lower() in file_name or keyword.lower() == file_ext:
                            # 创建目标文件夹
                            new_folder = target_path / folder_name
                            new_folder.mkdir(exist_ok=True)
                            
                            # 处理文件（移动或复制）
                            try:
                                # 如果目标文件已存在，添加数字后缀
                                target_file = new_folder / file_path.name
                                if target_file.exists():
                                    base_name = target_file.stem
                                    extension = target_file.suffix
                                    counter = 1
                                    while (new_folder / f"{base_name}_{counter}{extension}").exists():
                                        counter += 1
                                    target_file = new_folder / f"{base_name}_{counter}{extension}"
                                
                                # 根据操作模式选择移动或复制
                                operation_mode = self.mode_var.get()
                                if operation_mode == "move":
                                    shutil.move(str(file_path), str(target_file))
                                    operation_text = "已移动"
                                else:  # copy
                                    shutil.copy2(str(file_path), str(target_file))
                                    operation_text = "已复制"
                                
                                self.add_log(f"{operation_text}: {file_path.name} -> {folder_name}/")
                                self.processed_files += 1
                                matched = True
                                break
                            except Exception as e:
                                self.add_log(f"处理文件失败 {file_path.name}: {str(e)}")
                                self.error_files += 1
                    
                    if not matched:
                        self.skipped_files += 1
            
            # 打印统计信息
            self.add_log("\n整理完成！统计信息：")
            self.add_log(f"成功处理: {self.processed_files} 个文件")
            self.add_log(f"跳过: {self.skipped_files} 个文件")
            self.add_log(f"处理失败: {self.error_files} 个文件")
            
            # 更新状态
            self.status_var.set("完成")
            
        except Exception as e:
            self.add_log(f"处理文件时出错: {str(e)}")
            self.status_var.set("出错")
        
        finally:
            # 启用开始按钮
            self.start_btn.config(state=tk.NORMAL)
            self.is_processing = False
    
    def add_log(self, message):
        """添加日志"""
        # 添加到队列用于界面显示
        self.log_queue.put(message)
        # 同时写入日志文件
        logging.info(message)
    
    def update_log(self):
        """更新日志"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        
        # 每100毫秒检查一次
        self.root.after(100, self.update_log)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def save_log(self):
        """保存日志"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", "日志已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志时出错: {str(e)}")
    
    def import_rule_package(self):
        """导入规则包"""
        file_path = filedialog.askopenfilename(
            title="选择规则包文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    rule_package = json.load(f)
                
                # 验证规则包格式
                if not isinstance(rule_package, dict):
                    raise ValueError("规则包格式错误：不是有效的JSON对象")
                
                # 验证必需字段
                required_fields = ["version", "type", "created_at", "rules"]
                missing_fields = [field for field in required_fields if field not in rule_package]
                if missing_fields:
                    raise ValueError(f"规则包格式错误：缺少必需字段 {', '.join(missing_fields)}")
                
                # 验证规则包类型
                if rule_package["type"] != "file_organizer_rules":
                    raise ValueError("规则包格式错误：不是有效的文件整理助手规则包")
                
                # 验证规则数据
                rules = rule_package["rules"]
                if not isinstance(rules, dict):
                    raise ValueError("规则包格式错误：rules字段不是有效的规则对象")
                
                # 验证规则格式
                for keyword, folder in rules.items():
                    if not isinstance(keyword, str) or not isinstance(folder, str):
                        raise ValueError("规则包格式错误：规则数据格式不正确")
                    if not keyword or not folder:
                        raise ValueError("规则包格式错误：规则数据不能为空")
                
                # 询问是否覆盖现有规则
                if self.rules and messagebox.askyesno("确认", "是否覆盖现有规则？"):
                    self.rules = rules
                else:
                    # 合并规则
                    self.rules.update(rules)
                
                # 保存规则
                self.save_rules()
                self.refresh_rules_list()
                
                # 添加日志
                self.add_log(f"已导入规则包: {file_path}")
                self.add_log(f"规则包版本: {rule_package['version']}")
                self.add_log(f"创建时间: {rule_package['created_at']}")
                self.add_log(f"导入规则数量: {len(rules)}")
                
            except json.JSONDecodeError:
                messagebox.showerror("错误", "规则包格式错误：不是有效的JSON文件")
                self.add_log("导入规则包失败：不是有效的JSON文件")
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                self.add_log(f"导入规则包失败: {str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"导入规则包时出错: {str(e)}")
                self.add_log(f"导入规则包失败: {str(e)}")
    
    def export_rule_package(self):
        """导出规则包"""
        if not self.rules:
            messagebox.showinfo("提示", "当前没有规则可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存规则包",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 创建规则包数据
                rule_package = {
                    "version": "1.0",
                    "type": "file_organizer_rules",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rules": self.rules
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(rule_package, f, ensure_ascii=False, indent=4)
                
                # 添加日志
                self.add_log(f"已导出规则包: {file_path}")
                self.add_log(f"导出规则数量: {len(self.rules)}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出规则包时出错: {str(e)}")
                self.add_log(f"导出规则包失败: {str(e)}")

def main():
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 