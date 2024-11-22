import sqlite3
from dataclasses import dataclass
from typing import List, Optional
import json
import os
import uuid

@dataclass
class Prompt:
    id: Optional[int]  # 数据库自增ID
    uuid: str         # 全局唯一标识符
    title: str
    content: str
    category: str
    is_builtin: bool

class Database:
    def __init__(self):
        # 使用项目根目录下的数据库文件
        db_path = os.path.join(os.path.dirname(__file__), 'prompts.db')
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self.load_builtin_prompts()
        
    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                is_builtin BOOLEAN NOT NULL
            )
        ''')
        self.conn.commit()
    
    def save_prompt(self, prompt: Prompt) -> bool:
        try:
            if not prompt.uuid:
                prompt.uuid = str(uuid.uuid4())
            
            # 检查uuid是否已存在，如果存在就更新而不是插入
            cursor = self.conn.execute('SELECT id FROM prompts WHERE uuid = ?', (prompt.uuid,))
            existing_prompt = cursor.fetchone()
            
            if existing_prompt:
                # 更新现有记录
                self.conn.execute('''
                    UPDATE prompts 
                    SET title = ?, content = ?, category = ?, is_builtin = ?
                    WHERE uuid = ?
                ''', (prompt.title, prompt.content, prompt.category, prompt.is_builtin, prompt.uuid))
            else:
                # 插入新记录
                cursor = self.conn.execute(
                    '''INSERT INTO prompts 
                       (uuid, title, content, category, is_builtin) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (prompt.uuid, prompt.title, prompt.content, prompt.category, prompt.is_builtin)
                )
                prompt.id = cursor.lastrowid
                
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving prompt: {e}")
            return False
    
    def get_all_prompts(self) -> List[Prompt]:
        cursor = self.conn.execute('SELECT id, uuid, title, content, category, is_builtin FROM prompts')
        return [Prompt(*row) for row in cursor.fetchall()]
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Prompt]:
        cursor = self.conn.execute('SELECT id, uuid, title, content, category, is_builtin FROM prompts WHERE id = ?', (prompt_id,))
        row = cursor.fetchone()
        return Prompt(*row) if row else None
    
    def delete_prompt(self, prompt_id: int) -> bool:
        try:
            self.conn.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
            self.conn.commit()
            return True
        except:
            return False
    
    def update_prompt(self, prompt: Prompt) -> bool:
        try:
            self.conn.execute('''
                UPDATE prompts 
                SET title = ?, content = ?, category = ?
                WHERE id = ?
            ''', (prompt.title, prompt.content, prompt.category, prompt.id))
            self.conn.commit()
            return True
        except:
            return False

    def search_prompts(self, keyword: str) -> List[Prompt]:
        cursor = self.conn.execute('''
            SELECT id, uuid, title, content, category, is_builtin 
            FROM prompts 
            WHERE title LIKE ? OR content LIKE ?
        ''', (f'%{keyword}%', f'%{keyword}%'))
        return [Prompt(*row) for row in cursor.fetchall()]

    def load_builtin_prompts(self):
        try:
            # 先清除所有内置prompts
            self.conn.execute('DELETE FROM prompts WHERE is_builtin = 1')
            self.conn.commit()
                
            # 重新加载内置prompts
            builtin_file = os.path.join(os.path.dirname(__file__), 'builtin_prompts.json')
            if os.path.exists(builtin_file):
                with open(builtin_file, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    for p in prompts:
                        # 确保数据完整性
                        prompt = Prompt(
                            id=None,
                            uuid=p.get('uuid', str(uuid.uuid4())),
                            title=p.get('title', ''),
                            content=p.get('content', ''),
                            category=p.get('category', '通用'),
                            is_builtin=True
                        )
                        self.save_prompt(prompt)
        except Exception as e:
            print(f"Error loading builtin prompts: {e}")

    def export_prompts_to_json(self, prompts: List[Prompt]) -> List[dict]:
        """将Prompt对象转换为可序列化的字典列表"""
        return [{
            'uuid': p.uuid,
            'title': p.title,
            'content': p.content,
            'category': p.category,
            'is_builtin': p.is_builtin
        } for p in prompts]

    def get_filtered_prompts(self, filter_type: str) -> List[Prompt]:
        if filter_type == "所有Prompt":
            return self.get_all_prompts()
        elif filter_type == "内置Prompt":
            cursor = self.conn.execute('SELECT id, uuid, title, content, category, is_builtin FROM prompts WHERE is_builtin = 1')
            return [Prompt(*row) for row in cursor.fetchall()]
        else:  # 自定义Prompt
            cursor = self.conn.execute('SELECT id, uuid, title, content, category, is_builtin FROM prompts WHERE is_builtin = 0')
            return [Prompt(*row) for row in cursor.fetchall()]