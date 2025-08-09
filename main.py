# main.py
import time
import threading
import os
import torch
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import json
import numpy as np
import collections
import re

from audio_io import AudioRecorder
from stt_model import SpeechToText
from mt_model import MachineTranslator
from config import STT_MODELS, HF_TRANSLATION_MODELS, SAMPLE_RATE, BLOCK_SIZE, WHISPER_SILENCE_THRESHOLD,WHISPER_MAX_AUDIO_SECONDS
from ui.translator_ui import TranslatorUI


class RealtimeTranslatorApp:
    def __init__(self):
        self.recorder = None
        self.stt = None
        self.translator = None

        self._running = False
        self._audio_thread = None
        self._audio_buffer = collections.deque()
        self._last_speech_time = time.time()
        self._last_sent_time = time.time()  # 新增：记录上次发送给Whisper的时间

        self.current_input_device_id = None
        self.current_stt_model_name = None
        self.current_mt_model_name = None
        self._current_input_lang_code = None

        self.ui = TranslatorUI(
            start_callback=self.start_translation,
            stop_callback=self.stop_translation,
            save_callback=self.save_translated_text_to_file,
            get_audio_input_devices_callback=AudioRecorder.list_audio_input_devices,
            get_available_models_callback=self._get_available_models
        )
        self.ui.protocol("WM_DELETE_WINDOW", self.ui.on_closing)

    def _get_available_models(self):
        """Returns a list of available models for the UI dropdowns."""
        return STT_MODELS, HF_TRANSLATION_MODELS

    def _initialize_models(self, input_device_id: int, stt_model_name: str, mt_model_name: str):
        """Initializes models and recorder, ensuring they are loaded only when needed."""
        print(
            f"Initializing translator. Input Device ID: {input_device_id}, STT Model: {stt_model_name}, MT Model: {mt_model_name}")

        if self.recorder is None or self.recorder.device_id != input_device_id:
            if self.recorder:
                self.recorder.stop_recording()
            self.recorder = AudioRecorder(device_id=input_device_id, sample_rate=SAMPLE_RATE, block_size=BLOCK_SIZE)
        self.current_input_device_id = input_device_id

        if self.stt is None or self.current_stt_model_name != stt_model_name:
            self.stt = SpeechToText(model_name=stt_model_name, sample_rate=SAMPLE_RATE)
            self.current_stt_model_name = stt_model_name
            self._current_input_lang_code = STT_MODELS.get(stt_model_name, {}).get("code")

        if self.translator is None or self.current_mt_model_name != mt_model_name:
            mt_model_info = HF_TRANSLATION_MODELS.get(mt_model_name)
            if not mt_model_info:
                raise Exception(
                    f"Configuration error: Could not find information for translation model '{mt_model_name}'.")

            mt_src_lang = mt_model_info["src"]
            if self._current_input_lang_code and mt_src_lang != "multilingual" and mt_src_lang != self._current_input_lang_code:
                raise Exception(
                    f"Language mismatch: Recognition model '{self.current_stt_model_name}' (Language: {self._current_input_lang_code}) "
                    f"is incompatible with translation model '{mt_model_name}' (Source Language: {mt_src_lang}). Please select again.")

            self.translator = MachineTranslator(model_name=mt_model_name)
            self.current_mt_model_name = mt_model_name

    def _audio_processing_loop(self):
        """Audio processing loop running in a separate thread."""
        if self.stt.model_type == "vosk":
            self._vosk_processing_loop()
        elif self.stt.model_type == "whisper":
            self._whisper_processing_loop()
        else:
            print("Error: Unknown STT model type.")

    def _vosk_processing_loop(self):
        """Vosk streaming processing loop"""
        while self._running:
            audio_chunk = self.recorder.get_audio_chunk()
            if audio_chunk:
                timestamp = time.strftime("[%H:%M:%S] ")
                recognized_final = self.stt.recognizer.AcceptWaveform(audio_chunk)

                if recognized_final:
                    result_json = json.loads(self.stt.recognizer.Result())
                    final_text = result_json.get("text", "").strip()
                    if final_text:
                        self.ui.after(0, lambda: self.ui.append_recognized_text(timestamp + final_text, final=True))
                        if self.translator:
                            translated_text = self.translator.translate_text(final_text)
                            if translated_text:
                                self.ui.after(0, lambda: self.ui.append_translated_text(timestamp, final_text,
                                                                                        translated_text))
                else:
                    partial_result_json = json.loads(self.stt.recognizer.PartialResult())
                    partial_text = partial_result_json.get("partial", "").strip()
                    if partial_text:
                        self.ui.after(0, lambda: self.ui.append_recognized_text(timestamp + partial_text, final=False))
            else:
                time.sleep(0.01)

    def _whisper_processing_loop(self):
        """
        Whisper 非流式处理循环。
        最终优化逻辑：主要通过静默检测来触发识别，并用最大时长作为安全保障。
        """
        # 计算最大缓冲区大小（以采样点数为单位）
        max_buffer_size = WHISPER_MAX_AUDIO_SECONDS * SAMPLE_RATE

        while self._running:
            audio_chunk = self.recorder.get_audio_chunk()
            if audio_chunk:
                audio_np = np.frombuffer(audio_chunk, dtype='int16').astype(np.float32) / 32768.0

                # 只要检测到任何声音，就认为用户在说话，并更新最后说话时间
                if np.max(np.abs(audio_np)) > 0.05:  # 使用一个较低的音量阈值
                    self._last_speech_time = time.time()

                # 无论是否有声音，都将数据添加到缓冲区
                self._audio_buffer.append(audio_np)

            current_buffer_size = sum(len(a) for a in self._audio_buffer)
            time_since_last_speech = time.time() - self._last_speech_time

            # 触发条件 (满足任一即可):
            # 1. (主要) 缓冲区中有内容，且用户已停顿超过静默阈值。
            process_on_silence = self._audio_buffer and \
                                 (time_since_last_speech > WHISPER_SILENCE_THRESHOLD)

            # 2. (安全) 缓冲区中的音频时长已达到设定的最大值。
            process_on_max_length = self._audio_buffer and \
                                    (current_buffer_size >= max_buffer_size)

            if process_on_silence or process_on_max_length:
                self._process_whisper_buffer()
            else:
                # 避免CPU空转
                time.sleep(0.1)

        # 线程结束前，处理缓冲区中可能剩余的音频
        if self._audio_buffer:
            self._process_whisper_buffer()

    def _process_whisper_buffer(self):
        """Processes the audio buffer and sends it to the Whisper model."""
        audio_data = np.concatenate(list(self._audio_buffer))
        self._audio_buffer.clear()

        # 再次进行VAD检查，确保不是静默的音频块
        if np.max(np.abs(audio_data)) < 0.1:
            return

        if audio_data.size > 0:
            timestamp = time.strftime("[%H:%M:%S] ")

            # 在一个独立的线程中进行耗时的Whisper识别，以避免阻塞UI
            whisper_thread = threading.Thread(
                target=self._run_whisper_and_translate,
                args=(audio_data, timestamp),
                daemon=True
            )
            whisper_thread.start()

    def _run_whisper_and_translate(self, audio_data, timestamp):
        """Runs Whisper recognition and translation in a separate thread."""
        try:
            # 使用一个指示符来显示正在处理
            self.ui.after(0, lambda: self.ui.append_recognized_text(timestamp + "(Processing...)", final=False))
            final_text = self.stt.transcribe_full_audio_whisper(audio_data, language=self._current_input_lang_code)

            if final_text:
                self.ui.after(0, lambda: self.ui.append_recognized_text(timestamp + final_text, final=True))
                if self.translator:
                    translated_text = self.translator.translate_text(final_text)
                    if translated_text:
                        self.ui.after(0, lambda: self.ui.append_translated_text(timestamp, final_text, translated_text))
            else:
                self.ui.after(0, lambda: self.ui.append_recognized_text("", final=True))
        except Exception as e:
            self.ui.after(0, lambda: self.ui.append_recognized_text("", final=True))
            self.ui.after(0, lambda: messagebox.showerror("Whisper Error", f"Whisper recognition failed: {e}"))


    def start_translation(self, input_device_id: int, stt_model_name: str, mt_model_name: str):
        """Called from the UI thread to start the translation process."""
        if self._running:
            return

        try:
            self.ui.status_label.config(text="Status: Loading models...", fg="orange")
            self.ui.update_idletasks()

            self._initialize_models(input_device_id, stt_model_name, mt_model_name)

            self.recorder.start_recording()
            self._running = True
            self._audio_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
            self._audio_thread.start()

            self.ui.status_label.config(text="Status: Listening...", fg="blue")
            self.ui.start_button.config(state=tk.DISABLED)
            self.ui.stop_button.config(state=tk.NORMAL)
            self.ui.save_button.config(state=tk.NORMAL)
            self.ui.input_device_dropdown.config(state=tk.DISABLED)
            self.ui.stt_model_dropdown.config(state=tk.DISABLED)
            self.ui.mt_model_dropdown.config(state=tk.DISABLED)
            self.ui.clear_text_areas()
            print("Real-time translator started.")

        except Exception as e:
            messagebox.showerror("Startup Error",
                                 f"Failed to start translation:\n{e}\nPlease check model paths and dependencies.")
            print(f"Failed to start translator: {e}")
            self.stop_translation()

    def stop_translation(self):
        """Called from the UI thread to stop the translation process."""
        if not self._running:
            return

        print("Stopping real-time translator...")
        self._running = False
        if self._audio_thread:
            self._audio_thread.join(timeout=2)
            if self._audio_thread.is_alive():
                print("Warning: Audio processing thread did not stop in time.")

        if self.recorder:
            self.recorder.stop_recording()

        self.stt = None
        self.translator = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self.ui.status_label.config(text="Status: Stopped", fg="red")
        self.ui.start_button.config(state=tk.NORMAL)
        self.ui.stop_button.config(state=tk.DISABLED)
        self.ui.save_button.config(state=tk.DISABLED)
        self.ui.input_device_dropdown.config(state="readonly")
        self.ui.stt_model_dropdown.config(state="readonly")
        self.ui.mt_model_dropdown.config(state="readonly")
        print("Real-time translator stopped.")

    def save_translated_text_to_file(self):
        """Retrieves translated text from UI and saves it to a file."""
        recognized_content = self.ui.recognized_text.get("1.0", tk.END).strip()
        translated_content = self.ui.translated_text.get("1.0", tk.END).strip()

        if not recognized_content and not translated_content:
            messagebox.showwarning("Save Failed", "No content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="保存翻译结果"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(recognized_content + "\n" + translated_content)
                messagebox.showinfo("Save Successful", f"Content saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def run(self):
        """Runs the UI main loop."""
        self.ui.mainloop()


if __name__ == "__main__":
    app = RealtimeTranslatorApp()
    app.run()
