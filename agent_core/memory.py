import json
import os
from langchain_core.messages import messages_to_dict, messages_from_dict, SystemMessage

class MemoryManager:
    def __init__(self, file_path="data/chat_history.json"):
        self.file_path = file_path
        self.ensure_directory()

    def ensure_directory(self):
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_memory(self):
        """加载聊天记录，如果文件不存在则返回空列表"""
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return messages_from_dict(data)
        except Exception as e:
            print(f"⚠️  加载记忆失败: {e}，将开始新的会话。")
            return []

    def save_memory(self, messages):
        """保存聊天记录 (排除 SystemMessage，因为它通常由代码动态生成)"""
        # 过滤掉 SystemMessage，防止重复或过时
        conversation_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        
        try:
            data = messages_to_dict(conversation_messages)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存记忆失败: {e}")

    def clear_memory(self):
        """清除聊天记录"""
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                print("🧹 记忆已清除。")
            except Exception as e:
                print(f"⚠️  清除记忆失败: {e}")
        else:
            print("🧹 暂无记忆可清除。")
