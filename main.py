import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import json
import uuid
import os
from db import Database, Prompt

class PromptManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 初始化数据库
        self.db = Database()
        
        # 添加prompt存储字典
        self.prompt_cache = {}
        
        # 配置窗口
        self.title("Prompt 管理器")
        self.geometry("1000x600")
        
        # 创建变量
        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value="通用")
        self.filter_var = tk.StringVar(value="所有Prompt")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)  # 添加搜索变量监听
        
        # 配置窗口样式
        self.configure_window_style()
        
        # 创建界面
        self.create_gui()
        
        # 加载提示词
        self.load_prompts()
    
    def create_gui(self):
        # 创建主布局
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 创建侧边栏和主内容区
        self.create_sidebar()
        self.create_main_content()
    
    def create_sidebar(self):
        # 侧边栏框架
        sidebar = ctk.CTkFrame(
            self, 
            width=280,  # 增加宽度
            fg_color=("gray90", "gray16")  # 更深的背景色
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 搜索框容器
        search_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        search_frame.pack(fill=tk.X, padx=15, pady=(15,5))
        
        # 搜索图标和输入框在一行
        search_icon = ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=("Segoe UI", 14)
        )
        search_icon.pack(side=tk.LEFT, padx=(0,5))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="搜索提示词...",
            textvariable=self.search_var,
            height=35,
            corner_radius=8
        )
        search_entry.pack(fill=tk.X, expand=True)
        
        # 添加清除按钮
        clear_button = ctk.CTkButton(
            search_frame,
            text="✕",
            width=20,
            height=20,
            corner_radius=10,
            fg_color="transparent",
            hover_color=("gray75", "gray25"),
            command=self._clear_search
        )
        clear_button.pack(side=tk.RIGHT, padx=(5,0))
        self.clear_button = clear_button
        
        # 过滤器容器
        filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        filter_frame.pack(fill=tk.X, padx=15, pady=10)
        
        filters = (
            ("所有Prompt", "#3498DB"),  # 蓝色
            ("内置Prompt", "#2ECC71"),  # 绿色
            ("自定义Prompt", "#E67E22")  # 橙色
        )
        
        # 使用按钮组替代单选按钮
        for text, color in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                fg_color=color if self.filter_var.get() == text else "transparent",
                hover_color=self._adjust_color(color, -20),
                command=lambda t=text: self._on_filter_click(t),
                height=32,
                corner_radius=8,
                border_width=1,
                border_color=color,
                font=("Microsoft YaHei UI", 11)
            )
            btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        # 提示词列表标题
        list_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        list_header.pack(fill=tk.X, padx=15, pady=(20,5))
        
        list_label = ctk.CTkLabel(
            list_header,
            text="📝 提示词列表",
            font=("Microsoft YaHei UI", 14, "bold"),
            anchor="w"
        )
        list_label.pack(side=tk.LEFT)
        
        count_label = ctk.CTkLabel(
            list_header,
            text="0 个项目",
            font=("Microsoft YaHei UI", 11),
            text_color="gray60"
        )
        count_label.pack(side=tk.RIGHT)
        self.count_label = count_label  # 保存引用以便更新
        
        # 提示词列表容器（使用自定义Frame）
        list_container = PromptListFrame(
            sidebar,
            fg_color=("gray85", "gray20"),
            corner_radius=10,
            callback=self.on_select_prompt  # 传入回调函数
        )
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.prompt_list = list_container.listbox

    def _on_filter_click(self, filter_type):
        """处理过滤器按钮点击"""
        self.filter_var.set(filter_type)
        self.load_prompts()
        
        # 更新过滤器按钮状态
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                if widget.cget("text") == filter_type:
                    widget.configure(fg_color=widget.cget("border_color"))
                else:
                    widget.configure(fg_color="transparent")

    def create_main_content(self):
        # 主内容区框架
        main = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        
        # 标题和分类
        title_frame = ctk.CTkFrame(main, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="标题:",
            font=("Microsoft YaHei UI", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        title_entry = ctk.CTkEntry(
            title_frame,
            textvariable=self.title_var,
            height=32,
            font=("Microsoft YaHei UI", 11)
        )
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ctk.CTkLabel(
            title_frame,
            text="分类:",
            font=("Microsoft YaHei UI", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        category_entry = ctk.CTkEntry(
            title_frame,
            textvariable=self.category_var,
            width=120,
            height=32,
            font=("Microsoft YaHei UI", 11)
        )
        category_entry.pack(side=tk.LEFT, padx=5)
        
        # 按钮工具栏
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5,10))
        
        button_configs = [
            ("新建", "#2ECC71", self.new_prompt),      # 绿色
            ("保存", "#3498DB", self.save_prompt),      # 蓝色
            ("删除", "#E74C3C", self.delete_prompt),    # 红色
            ("导入", "#34495E", self.import_prompts),   # 深灰蓝色
            ("导出", "#34495E", self.export_prompts)    # 深灰蓝色
        ]
        
        for text, color, command in button_configs:
            ctk.CTkButton(
                btn_frame,
                text=text,
                command=command,
                width=100,
                height=32,
                fg_color=color,
                hover_color=self._adjust_color(color, -20),  # 暗化悬停颜色
                font=("Microsoft YaHei UI", 11)
            ).pack(side=tk.LEFT, padx=5)
        
        # 内容编辑区
        content_frame = ctk.CTkFrame(main, fg_color=("gray85", "gray25"))
        content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        self.content_text = ctk.CTkTextbox(
            content_frame,
            wrap="word",
            font=("Microsoft YaHei UI", 11),
            fg_color="transparent"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _on_search_changed(self, *args):
        """处理搜索文本变化"""
        search_text = self.search_var.get().strip()
        if search_text:
            # 执行搜索
            prompts = self.db.search_prompts(search_text)
            self._update_prompt_list(prompts)
            self.clear_button.configure(fg_color=("gray75", "gray35"))  # 显示清除按钮
        else:
            # 恢复显示所有prompt
            self.load_prompts()
            self.clear_button.configure(fg_color="transparent")  # 隐藏清除按钮

    def _clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.load_prompts()

    def _update_prompt_list(self, prompts):
        """更新提示词列表显示"""
        self.prompt_list.delete(0, tk.END)
        self.prompt_cache.clear()
        
        # 确保每行有足够的空间显示图标和标题
        max_title_len = max([len(p.title) for p in prompts]) if prompts else 0
        format_str = " {:<" + str(max_title_len + 4) + "}"
        
        for i, p in enumerate(prompts):
            # 添加项目，包括图标和固定宽度的格式
            icon = "📌" if p.is_builtin else "📝"
            display_text = format_str.format(f"{icon} {p.title}")
            self.prompt_list.insert(tk.END, display_text)
            self.prompt_cache[i] = p
            
            # 设置内置项目的特殊样式
            if p.is_builtin:
                self.prompt_list.itemconfig(
                    i,
                    fg="#4CAF50" if ctk.get_appearance_mode()=="light" else "#81C784"
                )
        
        # 更新计数
        count = len(prompts)
        self.count_label.configure(text=f"{count} 个项目")

    def load_prompts(self):
        """加载提示词列表"""
        filter_type = self.filter_var.get()
        prompts = self.db.get_filtered_prompts(filter_type)
        self._update_prompt_list(prompts)

    def on_select_prompt(self, event=None):
        """选择提示词时的处理"""
        selection = self.prompt_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        prompt = self.prompt_cache.get(index)
        
        if prompt:
            self.title_var.set(prompt.title)
            self.category_var.set(prompt.category)
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", prompt.content)
    
    def new_prompt(self):
        """新建提示词"""
        self.prompt_list.selection_clear(0, tk.END)
        self.title_var.set("")
        self.category_var.set("通用")
        self.content_text.delete("1.0", tk.END)

    def save_prompt(self):
        """保存当前prompt"""
        title = self.title_var.get().strip()
        category = self.category_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("提示", "标题和内容不能为空!")
            return
            
        # 获取当前选中的prompt(如果有)
        selection = self.prompt_list.curselection()
        prompt_id = None
        if selection:
            prompt = self.prompt_cache.get(selection[0])  # 从缓存中获取
            prompt_id = prompt.id if prompt else None
            
        # 创建新的prompt对象
        new_prompt = Prompt(
            id=prompt_id,
            uuid=str(uuid.uuid4()) if not prompt_id else None,
            title=title,
            content=content,
            category=category,
            is_builtin=False
        )
        
        # 保存到数据库
        if self.db.save_prompt(new_prompt):
            messagebox.showinfo("成功", "保存成功!")
            self.load_prompts()
        else:
            messagebox.showerror("错误", "保存失败!")

    def delete_prompt(self):
        """删除当前prompt"""
        selection = self.prompt_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        prompt = self.prompt_cache.get(index)  # 从缓存中获取
        if not prompt:
            return
            
        if prompt.is_builtin:
            messagebox.showwarning("提示", "内置Prompt不能删除!")
            return
            
        if messagebox.askyesno("确认", "确定要删除这个Prompt吗?"):
            if self.db.delete_prompt(prompt.id):
                messagebox.showinfo("成功", "删除成功!")
                self.load_prompts()
                self.new_prompt()  # 清空编辑区
            else:
                messagebox.showerror("错误", "删除失败!")

    def import_prompts(self):
        """从json文件导入prompts"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="选择要导入的JSON文件"
        )
        if not filename:
            return
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                
            success = 0
            for p in prompts:
                prompt = Prompt(
                    id=None,
                    uuid=p.get('uuid', str(uuid.uuid4())),
                    title=p.get('title', ''),
                    content=p.get('content', ''),
                    category=p.get('category', '通用'),
                    is_builtin=False
                )
                if self.db.save_prompt(prompt):
                    success += 1
                    
            self.load_prompts()
            messagebox.showinfo("成功", f"成功导入 {success} 个Prompt!")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_prompts(self):
        """导出prompts到json文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="选择保存位置"
        )
        if not filename:
            return
            
        try:
            filter_type = self.filter_var.get()
            prompts = self.db.get_filtered_prompts(filter_type)
            data = self.db.export_prompts_to_json(prompts)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("成功", "导出成功!")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    # 美化窗口
    def configure_window_style(self):
        """配置窗口样式"""
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 设置默认字体
        default_font = ("Microsoft YaHei UI", 10)  # 修改这里
        
        # 为不同组件设置字体
        self._apply_fonts(default_font)

    def _apply_fonts(self, font):
        """为所有需要的组件应用字体"""
        style_settings = {
            "*TLabel": {"font": font},
            "*TButton": {"font": font},
            "*TEntry": {"font": font},
            "*Text": {"font": font},
            "*Listbox": {"font": font},
        }
        
        for style, settings in style_settings.items():
            try:
                self.option_add(style, settings["font"])
            except Exception:
                pass

    def _adjust_color(self, hex_color: str, factor: int) -> str:
        """调整颜色深浅"""
        # 解析十六进制颜色
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # 调整颜色值
        r = max(0, min(255, r + factor))
        g = max(0, min(255, g + factor))
        b = max(0, min(255, b + factor))
        
        # 返回新的十六进制颜色
        return f"#{r:02x}{g:02x}{b:02x}"

class PromptListFrame(ctk.CTkFrame):
    def __init__(self, *args, callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.callback = callback
        
        # 创建滚动条
        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            self,
            selectmode=tk.SINGLE,
            activestyle='none',
            background=("#F0F0F0" if ctk.get_appearance_mode()=="light" else "#2A2A2A"),
            foreground=("black" if ctk.get_appearance_mode()=="light" else "white"),
            selectbackground=("#3498DB" if ctk.get_appearance_mode()=="light" else "#2980B9"),
            selectforeground="white",
            highlightthickness=0,
            bd=0,
            font=("Microsoft YaHei UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 配置滚动条
        scrollbar.config(command=self.listbox.yview)
        
        # 绑定事件
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        self.listbox.bind('<Motion>', self._on_motion)
        self.listbox.bind('<Leave>', self._on_leave)
        
        # 保存状态
        self._hover_item = None
        
    def _on_select(self, event):
        """处理选择事件"""
        if self.callback:
            self.callback(event)
    
    def _on_motion(self, event):
        """鼠标悬停效果"""
        index = self.listbox.nearest(event.y)
        if index != self._hover_item:
            # 恢复之前的悬停项
            if self._hover_item is not None:
                self._restore_item_color(self._hover_item)
            
            # 设置新的悬停项
            if not self.listbox.selection_includes(index):
                self.listbox.itemconfig(
                    index,
                    bg="#404040" if ctk.get_appearance_mode()=="dark" else "#E0E0E0"
                )
            self._hover_item = index
    
    def _on_leave(self, event):
        """鼠标离开效果"""
        if self._hover_item is not None:
            self._restore_item_color(self._hover_item)
            self._hover_item = None
    
    def _restore_item_color(self, index):
        """恢复项目原始颜色"""
        if not self.listbox.selection_includes(index):
            self.listbox.itemconfig(
                index,
                bg=self.listbox.cget("background")
            )

if __name__ == "__main__":
    app = PromptManager()
    app.mainloop()
