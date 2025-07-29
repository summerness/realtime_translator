# tts_model.py
import pyttsx3

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        # 可以设置语速和音量
        # self.engine.setProperty('rate', 150) # 语速 (words per minute)
        # self.engine.setProperty('volume', 0.9) # 音量 (0.0 to 1.0)
        print("TTS 引擎初始化完成。")

    def speak(self, text: str):
        """
        将文本转换为语音并播放。
        注意：pyttsx3 通常使用系统默认的音频输出设备，
        无法直接通过 sounddevice 的设备 ID 来控制具体的扬声器。
        如果你在UI中选择了扬声器，pyttsx3可能不会遵循。
        """
        if text.strip():
            print(f"TTS 播放: {text}")
            self.engine.say(text)
            self.engine.runAndWait() # 等待语音播放完毕

    def set_language_voice(self, lang_code: str):
        """
        尝试根据语言代码设置TTS语音。
        这依赖于系统安装的TTS语音包。
        """
        voices = self.engine.getProperty('voices')
        for voice in voices:
            # 尝试匹配语言代码，这里只是一个简单示例，可能需要更复杂的逻辑
            # 例如，对于中文，可能需要 'zh-cn' 或 'Chinese'
            # 对于英文，可能需要 'en-us' 或 'English'
            if lang_code.lower() in voice.lang.lower():
                self.engine.setProperty('voice', voice.id)
                print(f"TTS 语音设置为: {voice.name} ({voice.lang})")
                return
        print(f"未找到适合语言 '{lang_code}' 的 TTS 语音，将使用默认语音。")


if __name__ == "__main__":
    tts = TextToSpeech()
    tts.speak("Hello, this is a test of the text to speech functionality.")
    tts.set_language_voice("zh")
    tts.speak("你好，这是一个文本转语音的测试。")