# stt_model.py
from vosk import Model, KaldiRecognizer
import json
from config import VOSK_MODELS, SAMPLE_RATE
import os

class SpeechToText:
    def __init__(self, model_name: str, sample_rate=SAMPLE_RATE):
        self.model = None
        self.recognizer = None
        self.sample_rate = sample_rate
        self.load_model(model_name)

    def load_model(self, model_name: str):
        """根据模型名称加载Vosk模型"""
        model_info = VOSK_MODELS.get(model_name)
        if not model_info:
            raise Exception(f"未知的 Vosk 模型名称: {model_name}。请检查config.py。")

        model_path = model_info["path"]
        lang_code = model_info["code"] # 获取语言代码，可能有用

        if not os.path.exists(model_path):
            raise Exception(f"Vosk 模型路径不存在: {model_path} (模型: {model_name})。请下载模型并解压到此路径。")

        print(f"正在加载 Vosk 模型 ({model_name}): {model_path}...")
        # 释放旧模型资源 (如果存在)
        if self.recognizer:
            del self.recognizer
            self.recognizer = None
        if self.model:
            del self.model
            self.model = None

        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(False)
        print(f"Vosk 模型 ({model_name}) 加载成功。")

    # 移除了 transcribe_audio_chunk 方法

    def finalize_transcription(self) -> str:
        """
        在音频流结束时调用，以获取任何剩余的文本。
        """
        if not self.recognizer:
            return ""
        result = json.loads(self.recognizer.FinalResult())
        return result.get("text", "")


if __name__ == "__main__":
    try:
        stt_en = SpeechToText(model_name="Vosk 英文 (小)")
        print("英语 Vosk 模型测试成功。")
    except Exception as e:
        print(f"STT 模型加载失败: {e}")