# config.py

# Vosk 语音模型配置
# 格式: "UI显示名称": {"code": "语言代码", "path": "模型路径"}
# 请将 'path/to/your/vosk-model-small-en-us-0.15' 替换为你实际的模型路径
# 下载地址 https://alphacephei.com/vosk/models
VOSK_MODELS = {
    "Vosk 英文 (小)": {"code": "en", "path": "models/vosk-model-small-en-us-0.15"},
    "Vosk 中文 (小)": {"code": "zh", "path": "models/vosk-model-small-cn-0.22"},
    # 你可以添加更多Vosk模型，例如：
    # "Vosk 法文 (小)": {"code": "fr", "path": "models/vosk-model-small-fr-0.22"},
    # "Vosk 英文 (大)": {"code": "en", "path": "models/vosk-model-en-us-0.22"}, # 如果你下载了大模型
}

# Hugging Face 翻译模型配置
# 格式: "UI显示名称": {"src": "源语言代码", "tgt": "目标语言代码", "model_id": "HuggingFace模型ID"}
HF_TRANSLATION_MODELS = {
    "英文->中文 (Helsinki-NLP)": {"src": "en", "tgt": "zh", "model_path": "models/opus-mt-en-zh"},
    "中文->英文 (Helsinki-NLP)": {"src": "zh", "tgt": "en", "model_path": "models/opus-mt-zh-en"},
    # 你可以添加更多翻译模型，例如：
    # "英文->法文 (Helsinki-NLP)": {"src": "en", "tgt": "fr", "model_id": "Helsinki-NLP/opus-mt-en-fr"},
    # "多语言->英文 (M2M100-418M)": {"src": "multilingual", "tgt": "en", "model_id": "facebook/m2m100_418M"},
}

# 默认设置
DEFAULT_INPUT_LANGUAGE_MODEL = "Vosk 英文 (小)"  # 默认的STT模型显示名称
DEFAULT_TRANSLATION_MODEL = "英文->中文 (Helsinki-NLP)" # 默认的MT模型显示名称

# 音频配置 (保持不变)
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1