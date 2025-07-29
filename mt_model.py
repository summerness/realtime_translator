# mt_model.py
import os # 导入 os 模块，用于路径检查
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from config import HF_TRANSLATION_MODELS

class MachineTranslator:
    def __init__(self, model_name: str):
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.load_model(model_name)

    def load_model(self, model_name: str):
        """根据模型名称加载翻译模型"""
        model_info = HF_TRANSLATION_MODELS.get(model_name)
        if not model_info:
            raise Exception(f"未知的翻译模型名称: {model_name}。请检查config.py中的HF_TRANSLATION_MODELS。")

        # 从 config 中获取本地模型路径
        model_path = model_info["model_path"]

        # 检查本地模型路径是否存在
        if not os.path.exists(model_path):
            raise Exception(f"Hugging Face 模型路径不存在: {model_path} (模型: {model_name})。\n"
                            "请手动下载模型文件并放置到此路径。\n"
                            "您可以尝试先运行一次程序让其自动下载到缓存，然后将缓存中的模型文件复制过来。")

        print(f"正在加载翻译模型 ({model_name}): {model_path}...")
        # 释放旧模型资源 (如果存在)
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        if self.model:
            del self.model
            self.model = None
            if self.device == "cuda":
                torch.cuda.empty_cache() # 清理GPU缓存

        # 从本地路径加载模型和分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        print(f"翻译模型 ({model_name}) 加载完成，使用设备: {self.device}")

    def translate_text(self, text: str) -> str:
        if not text.strip() or not self.model:
            return ""

        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=512)

        translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated_text

if __name__ == "__main__":
    try:
        translator_en_zh = MachineTranslator(model_name="英文->中文 (Helsinki-NLP)")
        english_text = "Hello, how are you today?"
        chinese_text = translator_en_zh.translate_text(english_text)
        print(f"原文 (EN): {english_text}")
        print(f"译文 (ZH): {chinese_text}")
    except Exception as e:
        print(f"翻译模型加载或使用失败: {e}")
