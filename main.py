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
        sidebar = ctk.CTkFrame(self, width=200)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 过滤选项
        filter_label = ctk.CTkLabel(sidebar, text="过滤")
        filter_label.pack(pady=5)
        
        filters = ["所有Prompt", "内置Prompt", "自定义Prompt"]
        for f in filters:
            rb = ctk.CTkRadioButton(
                sidebar, 
                text=f,
                value=f,
                variable=self.filter_var,
                command=self.load_prompts
            )
            rb.pack(pady=2)
            
        # 提示词列表
        list_label = ctk.CTkLabel(sidebar, text="提示词列表")
        list_label.pack(pady=5)
        
        self.prompt_list = tk.Listbox(
            sidebar,
            width=25,
            height=20,
            selectmode=tk.SINGLE
        )
        self.prompt_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.prompt_list.bind('<<ListboxSelect>>', self.on_select_prompt)
    
    def create_main_content(self):
        # 主内容区框架
        main = ctk.CTkFrame(self)
        main.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        
        # 标题和分类
        title_frame = ctk.CTkFrame(main)
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(title_frame, text="标题:").pack(side=tk.LEFT, padx=5)
        title_entry = ctk.CTkEntry(title_frame, textvariable=self.title_var)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ctk.CTkLabel(title_frame, text="分类:").pack(side=tk.LEFT, padx=5)
        category_entry = ctk.CTkEntry(title_frame, textvariable=self.category_var)
        category_entry.pack(side=tk.LEFT, padx=5)
        
        # 按钮工具栏
        btn_frame = ctk.CTkFrame(main)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkButton(btn_frame, text="新建", command=self.new_prompt).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="保存", command=self.save_prompt).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="删除", command=self.delete_prompt).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="导入", command=self.import_prompts).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="导出", command=self.export_prompts).pack(side=tk.LEFT, padx=5)
        
        # 内容编辑区
        self.content_text = ctk.CTkTextbox(main, height=400)
        self.content_text.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

    def load_prompts(self):
        """加载提示词列表"""
        self.prompt_list.delete(0, tk.END)
        self.prompt_cache.clear()  # 清除缓存
        
        filter_type = self.filter_var.get()
        prompts = self.db.get_filtered_prompts(filter_type)
        
        for i, p in enumerate(prompts):
            self.prompt_list.insert(tk.END, p.title)
            self.prompt_cache[i] = p  # 使用索引存储prompt对象
    
    def on_select_prompt(self, event):
        """选择提示词时的处理"""
        selection = self.prompt_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        prompt = self.prompt_cache.get(index)  # 从缓存中获取prompt
        
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

if __name__ == "__main__":
    app = PromptManager()
    app.mainloop()
