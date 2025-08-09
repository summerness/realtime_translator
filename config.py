# config.py

# Vosk 语音模型配置
# 格式: "UI显示名称": {"code": "语言代码", "path": "模型路径"}
# 请将 'path/to/your/vosk-model-small-en-us-0.15' 替换为你实际的模型路径
# 下载地址 https://alphacephei.com/vosk/models
VOSK_MODELS = {
    "Vosk 美式英文 (大)": {"type": "vosk", "code": "en", "path": "models/vosk-model-small-en-us-0.15",
                           "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"},
    "Vosk 美式英文 (小)": {"type": "vosk", "code": "en", "path": "models/vosk-model-small-en-us-0.15",
                           "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"},
    "Vosk 印度英文 (大)": {"type": "vosk", "code": "en", "path": "models/vosk-model-en-in-0.5",
                           "url": "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip"},
    "Vosk 印度英文 (小)": {"type": "vosk", "code": "en", "path": "models/vosk-model-small-en-in-0.4",
                           "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"},
}

# Whisper 语音模型配置
# 格式: "UI显示名称": {"type": "whisper", "model_id": "模型ID"}
WHISPER_MODELS = {
    "Whisper 英文 (tiny)": {"type": "whisper", "model_path": "models/whisper-tiny.en",
                            "model_id": "openai/whisper-tiny.en", },
    "Whisper 英文 (small)": {"type": "whisper", "model_path": "models/whisper-small.en",
                             "model_id": "openai//whisper-small.en", },
    "Whisper 英文 (medium)": {"type": "whisper", "model_path": "models/whisper-medium.en",
                              "model_id": "openai/whisper-medium.en", },
    "Whisper 多语言 (tiny)": {"type": "whisper", "model_path": "models/whisper-tiny",
                              "model_id": "openai/whisper-tiny", },
    "Whisper 多语言 (small)": {"type": "whisper", "model_path": "models/whisper-small",
                               "model_id": "openai/whisper-small", },
    "Whisper 多语言 (medium)": {"type": "whisper", "model_path": "models/whisper-medium",
                                "model_id": "openai/whisper-medium", },
}

# 合并所有 STT 模型
STT_MODELS = {**VOSK_MODELS, **WHISPER_MODELS}

# Hugging Face 翻译模型配置
# 格式: "UI显示名称": {"src": "源语言代码", "tgt": "目标语言代码", "model_id": "HuggingFace模型ID"}
HF_TRANSLATION_MODELS = {
    "英文->中文 (Helsinki-NLP)": {"src": "en", "tgt": "zh", "model_path": "models/opus-mt-en-zh", "model_id": "Helsinki-NLP/opus-mt-en-zh",},

}

# 默认设置
DEFAULT_INPUT_LANGUAGE_MODEL = "Whisper 英文 (small)"  # 默认的STT模型显示名称
DEFAULT_TRANSLATION_MODEL = "英文->中文 (Helsinki-NLP)"  # 默认的MT模型显示名称

# 音频配置 (通常无需修改)
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1

WHISPER_SILENCE_THRESHOLD = 0.5

WHISPER_MAX_AUDIO_SECONDS = 20
