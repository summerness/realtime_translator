# download_manager.py
import os
import sys
import zipfile
import requests
from tqdm import tqdm
from huggingface_hub import snapshot_download


# --- 这是一个辅助类，让tqdm进度条能输出到我们的UI日志窗口 ---
class TqdmToGUILog:
    def __init__(self, logger):
        self.logger = logger
        self.buffer = ''

    def write(self, buf):
        # 清理字符串，只保留进度条本身
        self.buffer = buf.strip('\r\n\t ')

    def flush(self):
        # 换行符是tqdm完成一行输出的标志，确保实时更新
        if '\n' in self.buffer or '\r' in self.buffer:
            self.logger.write(self.buffer + '\n')


def download_hf_model_if_not_exists(model_id: str, local_path: str):
    """
    检查Hugging Face模型是否存在于本地路径，如果不存在则下载。
    """
    if os.path.exists(local_path) and os.listdir(local_path):
        print(f"Found model '{model_id}' locally at '{local_path}'. Skipping download.")
        return

    print(f"Model '{model_id}' not found locally. Downloading to '{local_path}'...")

    # 确保目标目录存在
    os.makedirs(local_path, exist_ok=True)

    try:
        # 使用snapshot_download下载整个模型仓库
        # 下载进度会自动打印到标准输出，也就是我们的UI日志窗口
        snapshot_download(
            repo_id=model_id,
            local_dir=local_path,
            local_dir_use_symlinks=False,  # 设置为False以复制文件而不是创建符号链接，增强可移植性
            resume_download=True
        )
        print(f"Successfully downloaded '{model_id}' to '{local_path}'.")
    except Exception as e:
        raise Exception(f"Failed to download model '{model_id}' from Hugging Face Hub: {e}")


def download_and_unzip_vosk_model(model_info):
    """下载并解压Vosk模型（此函数来自上次修改，逻辑不变）"""
    model_path = model_info["path"]
    model_url = model_info["url"]

    if os.path.exists(model_path):
        print(f"Vosk model folder already exists at: {model_path}")
        return

    print(f"Vosk model not found. Downloading from {model_url}...")
    zip_path = f"{model_path}.zip"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024

        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, file=TqdmToGUILog(sys.stdout))
        with open(zip_path, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()

        print("Download complete. Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(model_path))

        os.remove(zip_path)
        print(f"Model extracted to {model_path}")

    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise Exception(f"Failed to download or extract Vosk model: {e}")