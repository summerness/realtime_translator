# ui/translator_ui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog


class TranslatorUI(tk.Tk):
    def __init__(self, start_callback, stop_callback, save_callback, get_audio_input_devices_callback,
                 get_available_models_callback):
        super().__init__()
        self.title("实时翻译工具")
        self.geometry("950x700")

        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.save_callback = save_callback
        self.get_audio_input_devices_callback = get_audio_input_devices_callback
        self.get_available_models_callback = get_available_models_callback

        self.is_running = False
        self.last_recognized_text_is_final = True

        self._create_widgets()
        self._populate_device_dropdowns()
        self._populate_model_dropdowns()

    def _create_widgets(self):
        # --- Top Control Area ---
        control_frame = tk.Frame(self, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Audio Input Device Selection
        tk.Label(control_frame, text="音频输入设备:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.input_device_names = []
        self.input_device_ids = {}
        self.selected_input_device = tk.StringVar(self)
        self.input_device_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_input_device,
                                                  state="readonly", width=30)
        self.input_device_dropdown.pack(side=tk.LEFT, padx=5)
        self.input_device_dropdown.bind("<<ComboboxSelected>>", self._on_input_device_selected)

        # System Audio Input Hint
        system_audio_hint_frame = tk.Frame(self, padx=10, pady=0)
        system_audio_hint_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)
        tk.Label(system_audio_hint_frame,
                 text="提示：要翻译扬声器输出，请在“音频输入设备”中选择“立体声混音”或类似的设备（如果可用）。",
                 font=("Helvetica", 9), fg="gray").pack(side=tk.LEFT, padx=5, pady=(0, 5))

        # --- Model Selection Area ---
        model_frame = tk.Frame(self, padx=10, pady=5)
        model_frame.pack(side=tk.TOP, fill=tk.X)

        # STT Model Selection
        tk.Label(model_frame, text="识别模型:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.stt_model_names = []
        self.selected_stt_model = tk.StringVar(self)
        self.stt_model_dropdown = ttk.Combobox(model_frame, textvariable=self.selected_stt_model, state="readonly",
                                               width=20)
        self.stt_model_dropdown.pack(side=tk.LEFT, padx=5)
        self.stt_model_dropdown.bind("<<ComboboxSelected>>", self._on_stt_model_selected)

        # MT Model Selection
        tk.Label(model_frame, text="翻译模型:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=10)
        self.mt_model_names = []
        self.selected_mt_model = tk.StringVar(self)
        self.mt_model_dropdown = ttk.Combobox(model_frame, textvariable=self.selected_mt_model, state="readonly",
                                              width=25)
        self.mt_model_dropdown.pack(side=tk.LEFT, padx=5)
        self.mt_model_dropdown.bind("<<ComboboxSelected>>", self._on_mt_model_selected)

        # --- Buttons and Status Area ---
        button_status_frame = tk.Frame(self, padx=10, pady=5)
        button_status_frame.pack(side=tk.TOP, fill=tk.X)

        self.status_label = tk.Label(button_status_frame, text="状态: 未启动", font=("Helvetica", 12))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(button_status_frame, text="开始翻译", command=self.start_translation,
                                      font=("Helvetica", 12), bg="lightgreen", width=10)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_status_frame, text="停止翻译", command=self.stop_translation,
                                     font=("Helvetica", 12), bg="salmon", width=10, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(button_status_frame, text="保存翻译", command=self.save_translation_to_file,
                                     font=("Helvetica", 12), bg="lightblue", width=10)
        self.save_button.pack(side=tk.LEFT, padx=15)

        # --- Text Display Area ---
        text_frame = tk.Frame(self, padx=10, pady=10)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Recognized Text
        recognized_label = tk.Label(text_frame, text="识别文本:", font=("Helvetica", 12, "bold"))
        recognized_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        self.recognized_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10,
                                                         font=("Helvetica", 14), bg="white", fg="black")
        self.recognized_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.recognized_text.config(state=tk.DISABLED)

        # Translated Text
        translated_label = tk.Label(text_frame, text="翻译结果:", font=("Helvetica", 12, "bold"))
        translated_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        self.translated_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10,
                                                         font=("Helvetica", 14), bg="white", fg="black")
        self.translated_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.translated_text.config(state=tk.DISABLED)

    def _populate_device_dropdowns(self):
        """Populates the audio input device dropdown."""
        input_devices = self.get_audio_input_devices_callback()
        self.input_device_names = []
        self.input_device_ids = {}
        for dev in input_devices:
            display_name = f"{dev['name']} ({dev['hostapi']})"
            self.input_device_names.append(display_name)
            self.input_device_ids[display_name] = dev['id']

        self.input_device_dropdown['values'] = self.input_device_names
        if self.input_device_names:
            self.selected_input_device.set(self.input_device_names[0])

    def _populate_model_dropdowns(self):
        """Populates the STT and MT model dropdowns."""
        available_stt_models, available_mt_models = self.get_available_models_callback()

        # STT Models
        self.stt_model_names = sorted(list(available_stt_models.keys()))
        self.stt_model_dropdown['values'] = self.stt_model_names
        if self.stt_model_names:
            from config import DEFAULT_INPUT_LANGUAGE_MODEL
            if DEFAULT_INPUT_LANGUAGE_MODEL in self.stt_model_names:
                self.selected_stt_model.set(DEFAULT_INPUT_LANGUAGE_MODEL)
            else:
                self.selected_stt_model.set(self.stt_model_names[0])

        # MT Models
        self.mt_model_names = sorted(list(available_mt_models.keys()))
        self.mt_model_dropdown['values'] = self.mt_model_names
        if self.mt_model_names:
            from config import DEFAULT_TRANSLATION_MODEL
            if DEFAULT_TRANSLATION_MODEL in self.mt_model_names:
                self.selected_mt_model.set(DEFAULT_TRANSLATION_MODEL)
            else:
                self.selected_mt_model.set(self.mt_model_names[0])

    def _on_input_device_selected(self, event):
        print(f"Selected audio input device: {self.selected_input_device.get()}")

    def _on_stt_model_selected(self, event):
        print(f"Selected recognition model: {self.selected_stt_model.get()}")

    def _on_mt_model_selected(self, event):
        print(f"Selected translation model: {self.selected_mt_model.get()}")

    def start_translation(self):
        if self.is_running:
            return

        selected_input_device_name = self.selected_input_device.get()
        selected_input_device_id = self.input_device_ids.get(selected_input_device_name)
        selected_stt_model_name = self.selected_stt_model.get()
        selected_mt_model_name = self.selected_mt_model.get()

        if not selected_input_device_id:
            messagebox.showwarning("Selection Error", "Please select a valid audio input device.")
            return
        if not selected_stt_model_name:
            messagebox.showwarning("Selection Error", "Please select a recognition model.")
            return
        if not selected_mt_model_name:
            messagebox.showwarning("Selection Error", "Please select a translation model.")
            return

        try:
            self.start_callback(selected_input_device_id, selected_stt_model_name, selected_mt_model_name)
            self.is_running = True
            self.status_label.config(text="状态: 监听中...", fg="blue")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            self.input_device_dropdown.config(state=tk.DISABLED)
            self.stt_model_dropdown.config(state=tk.DISABLED)
            self.mt_model_dropdown.config(state=tk.DISABLED)
            self.clear_text_areas()
        except Exception as e:
            messagebox.showerror("Startup Error",
                                 f"Failed to start translation:\n{e}\nPlease check model paths and dependencies.")
            self.stop_translation()

    def stop_translation(self):
        if not self.is_running:
            return

        self.stop_callback()
        self.is_running = False
        self.status_label.config(text="状态: 已停止", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        self.input_device_dropdown.config(state="readonly")
        self.stt_model_dropdown.config(state="readonly")
        self.mt_model_dropdown.config(state="readonly")

    def save_translation_to_file(self):
        """Saves translated content to a file."""
        recognized_content = self.recognized_text.get("1.0", tk.END).strip()
        translated_content = self.translated_text.get("1.0", tk.END).strip()

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

    def display_recognized_text(self, full_content: str):
        self.recognized_text.config(state=tk.NORMAL)
        self.recognized_text.delete(1.0, tk.END)
        self.recognized_text.insert(tk.END, full_content)
        self.recognized_text.see(tk.END)
        self.recognized_text.config(state=tk.DISABLED)

    def append_recognized_text(self, text, final=False):
        self.recognized_text.config(state=tk.NORMAL)

        if not self.last_recognized_text_is_final:
            last_line_start_index = self.recognized_text.index("end-1c linestart")
            self.recognized_text.delete(last_line_start_index, tk.END)

        # 插入新文本
        if final:
            self.recognized_text.insert(tk.END, text + "\n\n")
            self.last_recognized_text_is_final = True
        else:
            # 对于临时结果，直接插入，不加换行符。
            self.recognized_text.insert(tk.END, text)
            # 标记下一条文本需要覆盖当前这行
            self.last_recognized_text_is_final = False

        self.recognized_text.see(tk.END)
        self.recognized_text.config(state=tk.DISABLED)

    def append_translated_text(self, timestamp, original_text, translated_text):
        self.translated_text.config(state=tk.NORMAL)
        content_to_add = f"{timestamp}原文: {original_text}\n{timestamp}译文: {translated_text}\n\n"
        self.translated_text.insert(tk.END, content_to_add)
        self.translated_text.see(tk.END)
        self.translated_text.config(state=tk.DISABLED)

    def clear_text_areas(self):
        self.recognized_text.config(state=tk.NORMAL)
        self.recognized_text.delete(1.0, tk.END)
        self.recognized_text.config(state=tk.DISABLED)
        self.last_recognized_text_is_final = True

        self.translated_text.config(state=tk.NORMAL)
        self.translated_text.delete(1.0, tk.END)
        self.translated_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.is_running:
            if messagebox.askyesno("退出", "翻译正在进行中，确定要退出吗？"):
                self.stop_translation()
                self.destroy()
        else:
            self.destroy()
