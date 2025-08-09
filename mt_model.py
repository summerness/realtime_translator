# mt_model.py
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from config import HF_TRANSLATION_MODELS

# 从我们自己的下载管理器导入函数
from download_manager import download_hf_model_if_not_exists


class MachineTranslator:
    def __init__(self, model_name: str):
        self.tokenizer = None
        self.model = None

        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.load_model(model_name)

    def load_model(self, model_name: str):
        model_info = HF_TRANSLATION_MODELS.get(model_name)
        if not model_info:
            raise Exception(f"Unknown translation model name: {model_name}.")

        model_id = model_info["model_id"]
        model_path = model_info["model_path"]

        print(f"Initializing translation model: {model_name}")

        if self.tokenizer: del self.tokenizer
        if self.model: del self.model
        if self.device == "cuda": torch.cuda.empty_cache()

        # 1. 调用下载器确保翻译模型存在
        print(f"Checking for translation model '{model_id}'...")
        download_hf_model_if_not_exists(model_id, model_path)

        print(f"Loading translation model from local path: '{model_path}'...")

        # 2. 从本地路径加载
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        print(f"Translation model '{model_name}' loaded successfully.")

    def translate_text(self, text: str) -> str:
        if not text.strip() or not self.model:
            return ""

        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=512)

        translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated_text
