
# 实时本地翻译工具

## 简介

这个项目是一个基于 Python 的实时语音翻译工具，它允许用户通过麦克风输入语音，将语音实时转换为文本（Speech-to-Text, STT），然后将识别到的文本翻译成指定的目标语言，并将结果显示在图形用户界面 (GUI) 上。该工具**完全使用本地模型**进行语音识别和机器翻译，无需互联网连接，保障了数据隐私和低延迟。

## 主要功能

* **实时语音输入：** 从默认或用户选择的麦克风实时捕获音频。

* **本地语音识别 (STT)：** 利用 **Vosk** 本地模型将实时语音转换为文本。

* **本地机器翻译 (MT)：** 利用 **Hugging Face Transformers** 库和本地预训练模型（如 MarianMT）将识别到的文本翻译成目标语言。

* **图形用户界面 (GUI)：** 基于 Tkinter 构建的用户友好界面，显示识别和翻译结果。

* **灵活的模型选择：** 用户可以在 UI 中选择不同的 STT 模型和 MT 模型（需提前配置和下载）。

* **设备选择：** 用户可以选择系统上可用的任何音频输入设备。

## 技术栈

* **Python 3.12以下**

* **`sounddevice`**: 用于音频输入/输出。

* **`vosk`**: 开源离线语音识别库。

* **`transformers`**: Hugging Face 的 NLP 库，用于加载和使用预训练的机器翻译模型。

* **`torch`**: PyTorch 深度学习框架，作为 `transformers` 的后端。

* **`numpy`**: 处理音频数据。

* **`tkinter`**: Python 标准 GUI 库。

## 安装与设置

### 1. 克隆仓库

首先，将项目仓库克隆到你的本地机器：

```bash
git clone https://github.com/your-username/realtime_translator.git # 请替换为你的实际仓库地址
cd realtime_translator
```
### 2.安装 Python 依赖
```bash
pip install sounddevice numpy vosk transformers torch sentencepiece
```

### 3. 下载并配置本地模型
#### 核心步骤！ 本工具依赖本地模型。你需要手动下载 Vosk 语音识别模型和Hugging Face 翻译模型，放在models文件夹下。
Vosk 语音识别模型下载地址：   
https://alphacephei.com/vosk/models  
Hugging Face模型：    
https://huggingface.co/Helsinki-NLP/opus-mt-zh-en   
https://huggingface.co/Helsinki-NLP/opus-mt-en-zh

## 这几个模型都较小，有时候识别效果不好，如果自己电脑的算力较好，可以换大的那个

### 3. 使用方法
运行应用程序：
在项目根目录下打开终端或命令行，然后运行：

```bash
python main.py
```

#### 选择设备和模型：   
应用程序启动后，将出现一个图形界面。

在 "麦克风" 下拉菜单中，选择你想要使用的音频输入设备。

在 "识别模型" 下拉菜单中，选择你说话的语言对应的 Vosk 模型。

在 "翻译模型" 下拉菜单中，选择你希望翻译到的目标语言模型。

#### 开始翻译：   
点击界面上的 "开始翻译" 按钮。程序将加载所选模型并开始监听你的麦克风。

说话并查看结果：   
对着麦克风说话。识别到的文本将实时显示在 "麦克风识别" 区域，翻译结果将显示在 "翻译结果" 区域。

#### 停止翻译：   
点击 "停止翻译" 按钮，或者直接关闭应用程序窗口，即可停止翻译过程。




