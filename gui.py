import os
import shutil
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from pathlib import Path
import threading
import queue
import webbrowser
from datetime import datetime, timedelta
import logging
from logging.handlers import TimedRotatingFileHandler
import time

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
        self.rule_groups = {
            "默认规则组": {}  # 默认规则组
        }
        self.current_group = "默认规则组"
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
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志保留天数设置
        days_frame = ttk.LabelFrame(main_frame, text="日志保留天数", padding="10")
        days_frame.pack(fill=tk.X, pady=(0, 10))
        
        days_var = tk.StringVar(value=str(self.log_retention_days))
        days_entry = ttk.Entry(days_frame, textvariable=days_var, width=10)
        days_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(days_frame, text="天").pack(side=tk.LEFT)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
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
        
        # 保存按钮
        save_btn = ttk.Button(btn_frame, text="保存", command=save_settings)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        # 取消按钮
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def load_rules(self):
        """加载已保存的分类规则"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rule_groups = data.get("rule_groups", {"默认规则组": {}})
                    self.current_group = data.get("current_group", "默认规则组")
            except json.JSONDecodeError:
                messagebox.showwarning("警告", "规则文件损坏，将创建新的规则文件")
                self.rule_groups = {"默认规则组": {}}
                self.current_group = "默认规则组"
        else:
            self.rule_groups = {"默认规则组": {}}
            self.current_group = "默认规则组"
    
    def save_rules(self):
        """保存分类规则"""
        try:
            data = {
                "rule_groups": self.rule_groups,
                "current_group": self.current_group
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"保存规则时出错: {str(e)}")
    
    def get_current_rules(self):
        """获取当前规则组的规则"""
        return self.rule_groups.get(self.current_group, {})
    
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
        """创建主界面组件"""
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 规则管理选项卡
        rules_frame = ttk.Frame(self.notebook)
        self.notebook.add(rules_frame, text="规则管理")
        self.setup_rules_tab(rules_frame)
        
        # 文件整理选项卡
        organize_frame = ttk.Frame(self.notebook)
        self.notebook.add(organize_frame, text="文件整理")
        self.setup_organize_tab(organize_frame)
        
        # 批量删除选项卡
        delete_frame = ttk.Frame(self.notebook)
        self.notebook.add(delete_frame, text="批量删除")
        self.setup_delete_tab(delete_frame)
        
        # 操作日志选项卡
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="操作日志")
        self.setup_log_tab(log_frame)
        
        # 关于选项卡
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="关于")
        self.setup_about_tab(about_frame)
    
    def setup_rules_tab(self, parent):
        """设置规则管理选项卡"""
        # 规则组选择框架
        group_frame = ttk.LabelFrame(parent, text="规则组", padding="10")
        group_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 规则组下拉框
        self.group_var = tk.StringVar(value=self.current_group)
        group_combo = ttk.Combobox(group_frame, textvariable=self.group_var, state="readonly")
        group_combo['values'] = list(self.rule_groups.keys())
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        group_combo.bind('<<ComboboxSelected>>', self.on_group_selected)
        
        # 规则组管理按钮
        ttk.Button(group_frame, text="管理规则组", command=self.show_group_management_dialog).pack(side=tk.RIGHT)
        
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
        
        # 添加规则按钮
        ttk.Button(btn_frame, text="添加规则", command=self.show_add_rule_dialog).pack(side=tk.LEFT, padx=5)
        
        # 修改规则按钮
        ttk.Button(btn_frame, text="修改规则", command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        
        # 删除规则按钮
        ttk.Button(btn_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        
        # 导入规则包按钮
        ttk.Button(btn_frame, text="导入规则包", command=self.import_rule_package).pack(side=tk.LEFT, padx=5)
        
        # 导出规则包按钮
        ttk.Button(btn_frame, text="导出规则包", command=self.export_rule_package).pack(side=tk.LEFT, padx=5)
        
        # 刷新规则列表
        self.refresh_rules_list()
    
    def on_group_selected(self, event):
        """规则组选择事件处理"""
        selected_group = self.group_var.get()
        if selected_group != self.current_group:
            self.current_group = selected_group
            self.save_rules()
            self.refresh_rules_list()
            self.add_log(f"已切换到规则组: {selected_group}")
    
    def show_group_management_dialog(self):
        """显示规则组管理对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("规则组管理")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使对话框居中显示
        self.center_window(dialog)
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则组列表框架
        list_frame = ttk.LabelFrame(main_frame, text="规则组列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 规则组列表
        group_tree = ttk.Treeview(list_frame, columns=("name",), show="headings", height=10)
        group_tree.heading("name", text="规则组名称")
        group_tree.column("name", width=300)
        group_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=group_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        group_tree.configure(yscrollcommand=scrollbar.set)
        
        # 刷新规则组列表
        def refresh_group_list():
            for item in group_tree.get_children():
                group_tree.delete(item)
            for group_name in self.rule_groups.keys():
                group_tree.insert("", tk.END, values=(group_name,))
                if group_name == self.current_group:
                    group_tree.selection_set(group_tree.get_children()[-1])
        
        refresh_group_list()
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        def add_group():
            name = simpledialog.askstring("添加规则组", "请输入规则组名称:", parent=dialog)
            if name:
                if name in self.rule_groups:
                    messagebox.showwarning("警告", f"规则组 '{name}' 已存在！", parent=dialog)
                    return
                self.rule_groups[name] = {}
                self.save_rules()
                refresh_group_list()
                self.add_log(f"已添加规则组: {name}")
        
        def delete_group():
            selected = group_tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择要删除的规则组！", parent=dialog)
                return
            
            group_name = group_tree.item(selected[0])['values'][0]
            if group_name == "默认规则组":
                messagebox.showwarning("警告", "不能删除默认规则组！", parent=dialog)
                return
            
            if messagebox.askyesno("确认", f"确定要删除规则组 '{group_name}' 吗？", parent=dialog):
                del self.rule_groups[group_name]
                if self.current_group == group_name:
                    self.current_group = "默认规则组"
                    self.group_var.set(self.current_group)
                self.save_rules()
                refresh_group_list()
                self.refresh_rules_list()
                self.add_log(f"已删除规则组: {group_name}")
        
        def rename_group():
            selected = group_tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择要重命名的规则组！", parent=dialog)
                return
            
            old_name = group_tree.item(selected[0])['values'][0]
            if old_name == "默认规则组":
                messagebox.showwarning("警告", "不能重命名默认规则组！", parent=dialog)
                return
            
            new_name = simpledialog.askstring("重命名", "请输入新的规则组名称:", 
                                             initialvalue=old_name, parent=dialog)
            if new_name and new_name != old_name:
                if new_name in self.rule_groups:
                    messagebox.showwarning("警告", f"规则组 '{new_name}' 已存在！", parent=dialog)
                    return
                
                # 重命名规则组
                self.rule_groups[new_name] = self.rule_groups.pop(old_name)
                
                # 更新当前规则组
                if self.current_group == old_name:
                    self.current_group = new_name
                    self.group_var.set(self.current_group)
                
                self.save_rules()
                refresh_group_list()
                self.refresh_rules_list()
                self.add_log(f"已将规则组 '{old_name}' 重命名为 '{new_name}'")
        
        # 按钮框架 - 使用网格布局
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 添加规则组按钮
        add_btn = ttk.Button(btn_frame, text="添加规则组", command=add_group)
        add_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 重命名规则组按钮
        rename_btn = ttk.Button(btn_frame, text="重命名", command=rename_group)
        rename_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 删除规则组按钮
        delete_btn = ttk.Button(btn_frame, text="删除规则组", command=delete_group)
        delete_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # 关闭按钮
        close_btn = ttk.Button(btn_frame, text="关闭", command=dialog.destroy)
        close_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # 配置列权重，使按钮均匀分布
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)
    
    def show_add_rule_dialog(self):
        """显示添加规则对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加规则")
        dialog.geometry("400x300")  # 增加窗口高度
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使对话框居中显示
        self.center_window(dialog)
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则组选择框架
        group_frame = ttk.LabelFrame(main_frame, text="规则组", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 规则组下拉框
        group_var = tk.StringVar(value=self.current_group)
        group_combo = ttk.Combobox(group_frame, textvariable=group_var, state="readonly")
        group_combo['values'] = list(self.rule_groups.keys())
        group_combo.pack(fill=tk.X, expand=True)
        
        # 关键词框架
        keyword_frame = ttk.LabelFrame(main_frame, text="关键词或文件扩展名", padding="10")
        keyword_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 关键词输入框
        keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(keyword_frame, textvariable=keyword_var, width=40)
        keyword_entry.pack(fill=tk.X, expand=True)
        
        # 目标文件夹框架
        folder_frame = ttk.LabelFrame(main_frame, text="目标文件夹名称 (留空则使用关键词)", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 目标文件夹输入框
        folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=40)
        folder_entry.pack(fill=tk.X, expand=True)
        
        # 按钮框架 - 使用网格布局
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 5))
        
        def add_rule():
            keyword = keyword_var.get().strip()
            folder = folder_var.get().strip()
            group_name = group_var.get()
            
            if not keyword:
                messagebox.showwarning("警告", "关键词不能为空！", parent=dialog)
                return
            
            # 如果文件夹名称为空，则使用关键词作为文件夹名称
            if not folder:
                folder = keyword
            
            # 规范化文件夹名称
            folder = folder.replace('/', '_').replace('\\', '_')
            
            # 添加规则
            self.rule_groups[group_name][keyword] = folder
            self.save_rules()
            self.refresh_rules_list()
            
            # 关闭对话框
            dialog.destroy()
            
            # 添加日志
            self.add_log(f"已在规则组 '{group_name}' 中添加规则: {keyword} -> {folder}")
        
        # 添加按钮 - 使用网格布局
        add_btn = ttk.Button(btn_frame, text="添加", command=add_rule)
        add_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 取消按钮 - 使用网格布局
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 配置列权重，使按钮均匀分布
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
    
    def refresh_rules_list(self):
        """刷新规则列表"""
        # 清空列表
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # 添加规则
        current_rules = self.get_current_rules()
        for keyword, folder in current_rules.items():
            self.rules_tree.insert("", tk.END, values=(keyword, folder))
    
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
                del self.rule_groups[self.current_group][keyword]
                self.add_log(f"已从规则组 '{self.current_group}' 中删除规则: {keyword}")
            
            self.save_rules()
            self.refresh_rules_list()
    
    def import_rule_package(self):
        """导入规则包"""
        file_path = filedialog.askopenfilename(
            title="选择规则包文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 验证规则包格式
                if not isinstance(data, dict):
                    raise ValueError("规则包格式错误：不是有效的JSON对象")
                
                # 验证必需字段
                required_fields = ["version", "type", "created_at", "rule_groups"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise ValueError(f"规则包格式错误：缺少必需字段 {', '.join(missing_fields)}")
                
                # 验证规则包类型
                if data["type"] != "file_organizer_rules":
                    raise ValueError("规则包格式错误：不是有效的文件整理助手规则包")
                
                # 验证规则组数据
                rule_groups = data["rule_groups"]
                if not isinstance(rule_groups, dict):
                    raise ValueError("规则包格式错误：rule_groups字段不是有效的规则组对象")
                
                # 验证规则组格式
                for group_name, rules in rule_groups.items():
                    if not isinstance(group_name, str) or not isinstance(rules, dict):
                        raise ValueError("规则包格式错误：规则组数据格式不正确")
                    for keyword, folder in rules.items():
                        if not isinstance(keyword, str) or not isinstance(folder, str):
                            raise ValueError("规则包格式错误：规则数据格式不正确")
                        if not keyword or not folder:
                            raise ValueError("规则包格式错误：规则数据不能为空")
                
                # 询问是否覆盖现有规则组
                if self.rule_groups and messagebox.askyesno("确认", "是否覆盖现有规则组？"):
                    self.rule_groups = rule_groups
                else:
                    # 合并规则组
                    for group_name, rules in rule_groups.items():
                        if group_name in self.rule_groups:
                            # 如果规则组已存在，询问是否覆盖
                            if messagebox.askyesno("确认", f"规则组 '{group_name}' 已存在，是否覆盖？"):
                                self.rule_groups[group_name] = rules
                            else:
                                # 不覆盖，合并规则
                                self.rule_groups[group_name].update(rules)
                        else:
                            # 如果规则组不存在，直接添加
                            self.rule_groups[group_name] = rules
                
                # 保存规则
                self.save_rules()
                self.refresh_rules_list()
                
                # 添加日志
                self.add_log(f"已导入规则包: {file_path}")
                self.add_log(f"规则包版本: {data['version']}")
                self.add_log(f"创建时间: {data['created_at']}")
                self.add_log(f"导入规则组数量: {len(rule_groups)}")
                
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
        if not self.rule_groups:
            messagebox.showinfo("提示", "当前没有规则组可导出")
            return
        
        # 生成默认文件名
        default_filename = f"FilesHelperRules_{datetime.now().strftime('%Y%m%d')}.json"
        
        file_path = filedialog.asksaveasfilename(
            title="保存规则包",
            defaultextension=".json",
            initialfile=default_filename,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 创建规则包数据
                data = {
                    "version": "1.0",
                    "type": "file_organizer_rules",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rule_groups": self.rule_groups
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                # 添加日志
                self.add_log(f"已导出规则包: {file_path}")
                self.add_log(f"导出规则组数量: {len(self.rule_groups)}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出规则包时出错: {str(e)}")
                self.add_log(f"导出规则包失败: {str(e)}")

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
        
        # 规则组选择框架
        group_frame = ttk.LabelFrame(parent, text="规则组", padding="10")
        group_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.organize_group_var = tk.StringVar(value=self.current_group)
        group_combo = ttk.Combobox(group_frame, textvariable=self.organize_group_var, state="readonly")
        group_combo['values'] = list(self.rule_groups.keys())
        group_combo.pack(fill=tk.X, expand=True)
        
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
        
        self.start_btn = ttk.Button(start_frame, text="开始整理", command=self.start_organize)
        self.start_btn.pack(side=tk.RIGHT)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, length=300, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(parent, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, padx=5)

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
        
        # 获取当前规则组
        group_name = self.organize_group_var.get()
        rules = self.rule_groups.get(group_name, {})
        
        # 检查是否有规则
        if not rules:
            messagebox.showwarning("警告", f"规则组 '{group_name}' 中没有规则")
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
        thread = threading.Thread(target=self.organize_files_thread, args=(source_dir, target_dir, group_name))
        thread.daemon = True
        thread.start()

    def organize_files_thread(self, source_dir, target_dir, group_name):
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
            self.add_log(f"使用规则组: {group_name}")
            self.status_var.set("正在处理...")
            
            # 获取规则组
            rules = self.rule_groups.get(group_name, {})
            
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
                    for keyword, folder_name in rules.items():
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

    def browse_source(self):
        """浏览选择源目录"""
        directory = filedialog.askdirectory(title="选择源目录")
        if directory:
            self.source_var.set(directory)
            self.add_log(f"已选择源目录: {directory}")

    def browse_target(self):
        """浏览选择目标目录"""
        directory = filedialog.askdirectory(title="选择目标目录")
        if directory:
            self.target_var.set(directory)
            self.add_log(f"已选择目标目录: {directory}")

    def setup_log_tab(self, parent):
        """设置日志选项卡"""
        # 日志显示区域
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置日志文本框只读
        self.log_text.config(state=tk.DISABLED)
        
        # 按钮框架
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 清除日志按钮
        clear_btn = ttk.Button(btn_frame, text="清除日志", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 日志设置按钮
        settings_btn = ttk.Button(btn_frame, text="日志设置", command=self.show_log_settings_dialog)
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加初始日志
        self.add_log("程序启动")
        self.add_log(f"当前日志保留天数: {self.log_retention_days} 天")

    def clear_log(self):
        """清除日志显示"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.add_log("日志已清除")

    def add_log(self, message):
        """添加日志"""
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化日志消息
        log_message = f"[{current_time}] {message}\n"
        
        # 添加到日志队列
        self.log_queue.put(log_message)
        
        # 同时记录到文件日志
        logging.info(message)
        
        # 更新日志显示
        self.update_log_display()

    def update_log_display(self):
        """更新日志显示"""
        try:
            # 获取所有待显示的日志
            while not self.log_queue.empty():
                log_message = self.log_queue.get_nowait()
                
                # 启用文本框编辑
                self.log_text.config(state=tk.NORMAL)
                
                # 插入日志消息
                self.log_text.insert(tk.END, log_message)
                
                # 滚动到最新位置
                self.log_text.see(tk.END)
                
                # 禁用文本框编辑
                self.log_text.config(state=tk.DISABLED)
                
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"更新日志显示时出错: {str(e)}")

    def setup_about_tab(self, parent):
        """设置关于选项卡"""
        # 关于信息框架
        about_frame = ttk.LabelFrame(parent, text="关于", padding="20")
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(about_frame, text="文件整理助手", style="Title.TLabel")
        title_label.pack(pady=(0, 10))
        
        # 版本信息
        version_label = ttk.Label(about_frame, text="版本: 1.0.0", style="Subtitle.TLabel")
        version_label.pack(pady=(0, 5))
        
        # 描述
        desc_label = ttk.Label(about_frame, text="一个帮助您自动整理文件的工具", style="Subtitle.TLabel")
        desc_label.pack(pady=(0, 20))
        
        # 开发者信息框架
        dev_frame = ttk.LabelFrame(about_frame, text="开发者信息", padding="10")
        dev_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 开发者名称
        name_label = ttk.Label(dev_frame, text="开发者: cxin")
        name_label.pack(anchor=tk.W, pady=2)
        
        # 开发者邮箱
        email_label = ttk.Label(dev_frame, text="邮箱: tojx@qq.com")
        email_label.pack(anchor=tk.W, pady=2)
        
        # 开发者网站
        website_label = ttk.Label(dev_frame, text="网站: www.cxin.net", style="Link.TLabel", cursor="hand2")
        website_label.pack(anchor=tk.W, pady=2)
        website_label.bind("<Button-1>", lambda e: webbrowser.open("http://www.cxin.net"))
        
        # 版权信息
        copyright_label = ttk.Label(about_frame, text="© 2024 cxin. All rights reserved.", style="Subtitle.TLabel")
        copyright_label.pack(side=tk.BOTTOM, pady=(20, 0))

    def update_log(self):
        """日志更新线程"""
        while True:
            try:
                # 更新日志显示
                self.update_log_display()
                # 每秒更新一次
                time.sleep(1)
            except Exception as e:
                logging.error(f"日志更新线程出错: {str(e)}")
                time.sleep(1)  # 出错时等待1秒后继续

    def show_edit_rule_dialog(self, keyword, folder):
        """显示修改规则对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改规则")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使对话框居中显示
        self.center_window(dialog)
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则组选择框架
        group_frame = ttk.LabelFrame(main_frame, text="规则组", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 规则组下拉框
        group_var = tk.StringVar(value=self.current_group)
        group_combo = ttk.Combobox(group_frame, textvariable=group_var, state="readonly")
        group_combo['values'] = list(self.rule_groups.keys())
        group_combo.pack(fill=tk.X, expand=True)
        
        # 关键词框架
        keyword_frame = ttk.LabelFrame(main_frame, text="关键词或文件扩展名", padding="10")
        keyword_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 关键词输入框
        keyword_var = tk.StringVar(value=keyword)
        keyword_entry = ttk.Entry(keyword_frame, textvariable=keyword_var, width=40)
        keyword_entry.pack(fill=tk.X, expand=True)
        
        # 目标文件夹框架
        folder_frame = ttk.LabelFrame(main_frame, text="目标文件夹名称 (留空则使用关键词)", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 目标文件夹输入框
        folder_var = tk.StringVar(value=folder)
        folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=40)
        folder_entry.pack(fill=tk.X, expand=True)
        
        # 按钮框架 - 使用网格布局
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 5))
        
        def save_rule():
            new_keyword = keyword_var.get().strip()
            new_folder = folder_var.get().strip()
            group_name = group_var.get()
            
            if not new_keyword:
                messagebox.showwarning("警告", "关键词不能为空！", parent=dialog)
                return
            
            # 如果文件夹名称为空，则使用关键词作为文件夹名称
            if not new_folder:
                new_folder = new_keyword
            
            # 规范化文件夹名称
            new_folder = new_folder.replace('/', '_').replace('\\', '_')
            
            # 如果关键词已更改，需要删除旧规则
            if new_keyword != keyword:
                del self.rule_groups[group_name][keyword]
            
            # 更新规则
            self.rule_groups[group_name][new_keyword] = new_folder
            self.save_rules()
            self.refresh_rules_list()
            
            # 关闭对话框
            dialog.destroy()
            
            # 添加日志
            self.add_log(f"已在规则组 '{group_name}' 中修改规则: {keyword} -> {new_keyword} -> {new_folder}")
        
        # 保存按钮 - 使用网格布局
        save_btn = ttk.Button(btn_frame, text="保存", command=save_rule)
        save_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 取消按钮 - 使用网格布局
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 配置列权重，使按钮均匀分布
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

    def edit_rule(self):
        """编辑选中的规则"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要修改的规则")
            return
        
        item = selected[0]
        values = self.rules_tree.item(item, "values")
        keyword = values[0]
        folder = values[1]
        
        self.show_edit_rule_dialog(keyword, folder)

    def setup_delete_tab(self, parent):
        """设置批量删除选项卡"""
        # 功能说明
        desc_frame = ttk.LabelFrame(parent, text="功能说明", padding="5")
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        desc_text = "此功能可以帮助您批量删除空目录和空文件。\n" \
                   "空目录：不包含任何文件和子目录的文件夹\n" \
                   "空文件：大小为0字节的文件"
        desc_label = ttk.Label(desc_frame, text=desc_text, wraplength=400)
        desc_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 源目录选择
        source_frame = ttk.LabelFrame(parent, text="源目录", padding="5")
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.delete_source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.delete_source_var)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(source_frame, text="浏览", command=self.browse_delete_source)
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # 删除选项
        options_frame = ttk.LabelFrame(parent, text="删除选项", padding="5")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(options_frame, text="递归处理子目录", 
                                        variable=self.recursive_var)
        recursive_check.pack(anchor=tk.W, padx=5, pady=2)
        
        self.delete_empty_dirs_var = tk.BooleanVar(value=True)
        empty_dirs_check = ttk.Checkbutton(options_frame, text="删除空目录", 
                                         variable=self.delete_empty_dirs_var)
        empty_dirs_check.pack(anchor=tk.W, padx=5, pady=2)
        
        self.delete_empty_files_var = tk.BooleanVar(value=True)
        empty_files_check = ttk.Checkbutton(options_frame, text="删除空文件", 
                                          variable=self.delete_empty_files_var)
        empty_files_check.pack(anchor=tk.W, padx=5, pady=2)
        
        self.confirm_delete_var = tk.BooleanVar(value=True)
        confirm_check = ttk.Checkbutton(options_frame, text="删除前确认", 
                                      variable=self.confirm_delete_var)
        confirm_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 开始按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_delete_button = ttk.Button(button_frame, text="开始删除", 
                                            command=self.start_delete)
        self.start_delete_button.pack(side=tk.RIGHT, padx=5)
        
        # 进度条
        self.delete_progress = ttk.Progressbar(parent, mode='determinate')
        self.delete_progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态标签
        self.delete_status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(parent, textvariable=self.delete_status_var)
        status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 初始化计数器
        self.deleted_dirs = 0
        self.deleted_files = 0
        self.delete_errors = 0
        
    def browse_delete_source(self):
        """浏览选择源目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.delete_source_var.set(directory)
            self.add_log(f"选择源目录: {directory}")
            
    def start_delete(self):
        """开始删除操作"""
        source_dir = self.delete_source_var.get()
        if not source_dir:
            messagebox.showerror("错误", "请选择源目录")
            return
            
        if not os.path.exists(source_dir):
            messagebox.showerror("错误", "源目录不存在")
            return
            
        if not self.delete_empty_dirs_var.get() and not self.delete_empty_files_var.get():
            messagebox.showerror("错误", "请至少选择一种删除类型")
            return
            
        if self.confirm_delete_var.get():
            if not messagebox.askyesno("确认", "确定要开始删除操作吗？此操作不可撤销！"):
                return
                
        self.start_delete_button.configure(state=tk.DISABLED)
        self.delete_progress['value'] = 0
        self.delete_status_var.set("正在删除...")
        self.deleted_dirs = 0
        self.deleted_files = 0
        self.delete_errors = 0
        
        # 在新线程中执行删除操作
        threading.Thread(target=self.delete_items_thread, args=(source_dir,), daemon=True).start()
        
    def delete_items_thread(self, source_dir):
        """删除线程"""
        try:
            # 获取所有目录和文件
            all_items = []
            for root, dirs, files in os.walk(source_dir, topdown=False):
                if not self.recursive_var.get() and root != source_dir:
                    continue
                    
                if self.delete_empty_dirs_var.get():
                    all_items.extend([os.path.join(root, d) for d in dirs])
                    
                if self.delete_empty_files_var.get():
                    all_items.extend([os.path.join(root, f) for f in files])
                    
            total_items = len(all_items)
            if total_items == 0:
                self.delete_status_var.set("没有找到需要删除的项目")
                self.start_delete_button.configure(state=tk.NORMAL)
                return
                
            # 处理每个项目
            for i, item in enumerate(all_items, 1):
                try:
                    if os.path.isdir(item):
                        # 检查是否为空目录
                        if not os.listdir(item):
                            os.rmdir(item)
                            self.deleted_dirs += 1
                            self.add_log(f"删除空目录: {item}")
                    else:
                        # 检查是否为空文件
                        if os.path.getsize(item) == 0:
                            os.remove(item)
                            self.deleted_files += 1
                            self.add_log(f"删除空文件: {item}")
                            
                except Exception as e:
                    self.delete_errors += 1
                    self.add_log(f"删除失败: {item} - {str(e)}")
                    
                # 更新进度
                progress = (i / total_items) * 100
                self.delete_progress['value'] = progress
                self.delete_status_var.set(f"正在处理: {i}/{total_items}")
                
            # 完成
            status = f"删除完成 - 目录: {self.deleted_dirs}, 文件: {self.deleted_files}"
            if self.delete_errors > 0:
                status += f", 错误: {self.delete_errors}"
            self.delete_status_var.set(status)
            self.add_log(status)
            
        except Exception as e:
            self.delete_status_var.set(f"删除过程出错: {str(e)}")
            self.add_log(f"删除过程出错: {str(e)}")
            
        finally:
            self.start_delete_button.configure(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 