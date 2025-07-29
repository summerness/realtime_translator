# main.py
import time
import threading
import os
import torch
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from audio_io import AudioRecorder
from stt_model import SpeechToText
from mt_model import MachineTranslator
from config import VOSK_MODELS, HF_TRANSLATION_MODELS, SAMPLE_RATE, BLOCK_SIZE
from ui.translator_ui import TranslatorUI
import json  # 导入 json 模块


class RealtimeTranslatorApp:
    def __init__(self):
        self.recorder = None
        self.stt = None
        self.translator = None

        self._running = False
        self._audio_thread = None

        self.current_input_device_id = None

        self.current_stt_model_name = None
        self.current_mt_model_name = None
        self._current_input_lang_code = None

        self.ui = TranslatorUI(
            start_callback=self.start_translation,
            stop_callback=self.stop_translation,
            get_audio_input_devices_callback=AudioRecorder.list_audio_input_devices,
            get_available_models_callback=self._get_available_models,
            save_callback=self.save_translated_text_to_file,
        )
        self.ui.protocol("WM_DELETE_WINDOW", self.ui.on_closing)

    def save_translated_text_to_file(self):
        """Retrieves translated text from UI and saves it to a file."""
        translated_content = self.ui.translated_text.get("1.0", tk.END).strip()
        if not translated_content:
            messagebox.showwarning("Save Failed", "No translated content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Translated Text"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(translated_content)
                messagebox.showinfo("Save Successful", f"Translated content saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def _get_available_models(self):
        """返回可用模型列表，供UI下拉菜单使用"""
        return VOSK_MODELS, HF_TRANSLATION_MODELS

    # 移除 output_device_id 参数
    def _initialize_models(self, input_device_id: int, stt_model_name: str, mt_model_name: str):
        """初始化模型和录音器，确保只在需要时加载"""
        # 移除输出设备ID的打印
        print(f"初始化翻译器，输入设备ID: {input_device_id}, STT模型: {stt_model_name}, MT模型: {mt_model_name}")

        if self.recorder is None or self.recorder.device_id != input_device_id:
            if self.recorder:
                self.recorder.stop_recording()
            self.recorder = AudioRecorder(device_id=input_device_id, sample_rate=SAMPLE_RATE, block_size=BLOCK_SIZE)
        self.current_input_device_id = input_device_id

        if self.stt is None or self.current_stt_model_name != stt_model_name:
            self.stt = SpeechToText(model_name=stt_model_name, sample_rate=SAMPLE_RATE)
            self.current_stt_model_name = stt_model_name
            self._current_input_lang_code = VOSK_MODELS.get(stt_model_name, {}).get("code")

        if self.translator is None or self.current_mt_model_name != mt_model_name:
            mt_model_info = HF_TRANSLATION_MODELS.get(mt_model_name)
            if not mt_model_info:
                raise Exception(f"配置错误: 无法找到翻译模型 '{mt_model_name}' 的信息。")

            mt_src_lang = mt_model_info["src"]
            if self._current_input_lang_code and mt_src_lang != "multilingual" and mt_src_lang != self._current_input_lang_code:
                raise Exception(
                    f"语言不匹配: 识别模型 '{self.current_stt_model_name}' (语言: {self._current_input_lang_code}) "
                    f"与翻译模型 '{mt_model_name}' (源语言: {mt_src_lang}) 不兼容。请重新选择。")

            self.translator = MachineTranslator(model_name=mt_model_name)
            self.current_mt_model_name = mt_model_name

    def _audio_processing_loop(self):
        """在单独的线程中运行的音频处理循环"""
        while self._running:
            audio_chunk = self.recorder.get_audio_chunk()
            if audio_chunk:
                # 核心改动：只调用一次 AcceptWaveform，并根据其返回值处理结果
                recognized_final = self.stt.recognizer.AcceptWaveform(audio_chunk)

                if recognized_final:
                    # 获取最终结果
                    result_json = json.loads(self.stt.recognizer.Result())
                    final_text = result_json.get("text", "").strip()
                    # --- 调试信息：检查Vosk最终识别结果 ---
                    # if final_text:
                    #     print(f"Vosk Final: '{final_text}'")
                    if final_text:
                        self.ui.after(0, lambda: self.ui.append_recognized_text(final_text))  # 直接传递最终文本
                        if self.translator:
                            translated_text = self.translator.translate_text(final_text)
                            if translated_text:
                                self.ui.after(0, lambda: self.ui.append_translated_text(
                                    "{}:\n{}".format(final_text, translated_text)))
                else:
                    # 获取部分结果
                    partial_result_json = json.loads(self.stt.recognizer.PartialResult())
                    partial_text = partial_result_json.get("partial", "").strip()
                    # --- 调试信息：检查Vosk部分识别结果 ---
                    # if partial_text:
                    #     print(f"Vosk Partial: '{partial_text}'")
                    if partial_text:  # 只有当有实际的partial文本时才更新UI
                        # 为部分结果添加前缀，并传递给UI
                        self.ui.after(0, lambda: self.ui.append_recognized_text(" (Partial) " + partial_text))
            else:
                time.sleep(0.01)

    def _update_recognized_text_ui(self, text, final=False):
        """
        这个函数在新的逻辑中不再直接使用，
        因为append_recognized_text已经处理了部分和最终结果的逻辑。
        为了避免混淆，暂时保留但不会被调用。
        """
        pass

    # 移除 output_device_id 参数
    def start_translation(self, input_device_id: int, stt_model_name: str, mt_model_name: str):
        """在 UI 线程中调用，启动翻译流程"""
        if self._running:
            return

        try:
            self.ui.status_label.config(text="状态: 正在加载模型...", fg="orange")
            self.ui.update_idletasks()

            # 移除 output_device_id 参数
            self._initialize_models(input_device_id, stt_model_name, mt_model_name)

            self.recorder.start_recording()
            self._running = True
            self._audio_thread = threading.Thread(target=self._audio_processing_loop)
            self._audio_thread.daemon = True
            self._audio_thread.start()

            self.ui.status_label.config(text="状态: 监听中...", fg="blue")
            self.ui.start_button.config(state=tk.DISABLED)
            self.ui.stop_button.config(state=tk.NORMAL)
            self.ui.input_device_dropdown.config(state=tk.DISABLED)
            # self.ui.output_device_dropdown.config(state=tk.DISABLED) # 移除禁用输出设备选择
            self.ui.stt_model_dropdown.config(state=tk.DISABLED)
            self.ui.mt_model_dropdown.config(state=tk.DISABLED)
            self.ui.clear_text_areas()
            print("实时翻译器已启动。")

        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动翻译：\n{e}\n请检查模型路径和依赖项。")
            print(f"启动翻译器失败: {e}")
            self.stop_translation()

    def stop_translation(self):
        """在 UI 线程中调用，停止翻译流程"""
        if not self._running:
            return

        print("停止实时翻译器...")
        self._running = False
        if self._audio_thread:
            self._audio_thread.join(timeout=2)
            if self._audio_thread.is_alive():
                print("警告: 音频处理线程未能及时停止。")

        if self.recorder:
            self.recorder.stop_recording()

        self.stt = None
        self.translator = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self.ui.status_label.config(text="状态: 已停止", fg="red")
        self.ui.start_button.config(state=tk.NORMAL)
        self.ui.stop_button.config(state=tk.DISABLED)
        self.ui.input_device_dropdown.config(state="readonly")
        self.ui.stt_model_dropdown.config(state="readonly")
        self.ui.mt_model_dropdown.config(state="readonly")
        print("实时翻译器已停止。")

    def run(self):
        """运行 UI 主循环"""
        self.ui.mainloop()


if __name__ == "__main__":
    app = RealtimeTranslatorApp()
    app.run()
