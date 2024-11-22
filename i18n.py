
import json
import os

class I18n:
    def __init__(self):
        self.current_lang = "zh"
        self.translations = self._load_translations()
    
    def _load_translations(self):
        """加载翻译文件"""
        translations = {}
        i18n_dir = os.path.join(os.path.dirname(__file__), 'i18n')
        
        for lang in ['zh', 'en']:
            file_path = os.path.join(i18n_dir, f'{lang}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
        
        return translations
    
    def t(self, key: str) -> str:
        """获取翻译文本"""
        try:
            keys = key.split('.')
            value = self.translations[self.current_lang]
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return key
    
    def set_language(self, lang: str):
        """设置当前语言"""
        if lang in self.translations:
            self.current_lang = lang