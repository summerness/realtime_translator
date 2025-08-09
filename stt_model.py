# stt_model.py
import os
import json
from vosk import Model, KaldiRecognizer
import torch
import numpy as np
from transformers import pipeline
from config import STT_MODELS, SAMPLE_RATE
from download_manager import download_hf_model_if_not_exists, download_and_unzip_vosk_model

class SpeechToText:
    def __init__(self, model_name: str, sample_rate=SAMPLE_RATE):
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.model_type = STT_MODELS.get(model_name, {}).get("type")
        self.recognizer = None
        self.pipe = None
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        self.load_model(model_name)

    def load_model(self, model_name: str):
        model_info = STT_MODELS.get(model_name)
        if not model_info:
            raise Exception(f"Unknown STT model name: {model_name}.")

        self.model_type = model_info.get("type")

        print(f"Initializing STT model: {model_name}")

        self.recognizer = None
        self.pipe = None
        if self.device == "cuda":
            torch.cuda.empty_cache()

        if self.model_type == "vosk":
            # 1. 调用下载器确保Vosk模型存在
            download_and_unzip_vosk_model(model_info)
            model_path = model_info.get("path")
            # 2. 从本地路径加载
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(False)

        elif self.model_type == "whisper":
            model_id = model_info.get("model_id")
            model_path = model_info.get("model_path")

            # 1. 调用下载器确保Whisper模型存在
            print(f"Checking for Whisper model '{model_id}'...")
            download_hf_model_if_not_exists(model_id, model_path)

            print(f"Loading Whisper model from local path: '{model_path}'...")
            try:
                # 2. 从本地路径加载
                self.pipe = pipeline(
                    "automatic-speech-recognition",
                    model=model_path,
                    chunk_length_s=30,
                    device=self.device
                )
                self.pipe.model.config.forced_decoder_ids = None
            except Exception as e:
                raise Exception(f"Failed to load Whisper model from local path: {e}")
        else:
            raise Exception(f"Unsupported STT model type: {self.model_type}")

        print(f"STT model '{model_name}' loaded successfully.")

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribes audio data using the Vosk model."""
        if self.model_type != "vosk":
            raise TypeError("This method is only for Vosk models.")

        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            return result.get("text", "")
        else:
            partial_result = json.loads(self.recognizer.PartialResult())
            return partial_result.get("partial", "")

    def transcribe_full_audio_whisper(self, audio_data: list, language: str = None) -> str:
        if self.model_type != "whisper":
            raise TypeError("This method is only for Whisper models.")

        if not self.pipe:
            return ""

        transcription = self.pipe(audio_data, generate_kwargs={"language": language})
        return transcription.get('text', "")

    def finalize_transcription(self) -> str:
        """Gets the final result from the Vosk recognizer."""
        if self.model_type == "vosk" and self.recognizer:
            result = json.loads(self.recognizer.FinalResult())
            return result.get("text", "")
        return ""

