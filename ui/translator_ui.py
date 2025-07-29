# ui/translator_ui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog # 导入 filedialog

class TranslatorUI(tk.Tk):
    def __init__(self, start_callback, stop_callback, save_callback, get_audio_input_devices_callback, get_available_models_callback): # 新增 save_callback
        super().__init__()
        self.title("实时翻译工具")
        self.geometry("950x700")

        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.save_callback = save_callback # 保存回调
        self.get_audio_input_devices_callback = get_audio_input_devices_callback
        self.get_available_models_callback = get_available_models_callback

        self.is_running = False

        self._create_widgets()
        self._populate_device_dropdowns()
        self._populate_model_dropdowns()

    def _create_widgets(self):
        # --- 顶部控制区域 ---
        control_frame = tk.Frame(self, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # 音频输入设备选择 (合并后的下拉菜单)
        tk.Label(control_frame, text="音频输入设备:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.input_device_names = []
        self.input_device_ids = {}
        self.selected_input_device = tk.StringVar(self)
        self.input_device_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_input_device, state="readonly", width=30)
        self.input_device_dropdown.pack(side=tk.LEFT, padx=5)
        self.input_device_dropdown.bind("<<ComboboxSelected>>", self._on_input_device_selected)

        # 系统音频输入提示
        system_audio_hint_frame = tk.Frame(self, padx=10, pady=0)
        system_audio_hint_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)
        tk.Label(system_audio_hint_frame, text="提示：要翻译扬声器输出，请在“音频输入设备”中选择“立体声混音”或类似的设备（如果可用）。",
                 font=("Helvetica", 9), fg="gray").pack(side=tk.LEFT, padx=5, pady=(0, 5))


        # --- 模型选择区域 ---
        model_frame = tk.Frame(self, padx=10, pady=5)
        model_frame.pack(side=tk.TOP, fill=tk.X)

        # STT 模型选择
        tk.Label(model_frame, text="识别模型:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.stt_model_names = []
        self.selected_stt_model = tk.StringVar(self)
        self.stt_model_dropdown = ttk.Combobox(model_frame, textvariable=self.selected_stt_model, state="readonly", width=20)
        self.stt_model_dropdown.pack(side=tk.LEFT, padx=5)
        self.stt_model_dropdown.bind("<<ComboboxSelected>>", self._on_stt_model_selected)

        # MT 模型选择
        tk.Label(model_frame, text="翻译模型:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=10)
        self.mt_model_names = []
        self.selected_mt_model = tk.StringVar(self)
        self.mt_model_dropdown = ttk.Combobox(model_frame, textvariable=self.selected_mt_model, state="readonly", width=25)
        self.mt_model_dropdown.pack(side=tk.LEFT, padx=5)
        self.mt_model_dropdown.bind("<<ComboboxSelected>>", self._on_mt_model_selected)

        # --- 按钮和状态区域 ---
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

        self.save_button = tk.Button(button_status_frame, text="保存翻译", command=self.save_translation_to_file, # 新增保存按钮
                                     font=("Helvetica", 12), bg="lightblue", width=10, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=15) # 稍微增加间距


        # --- 文本显示区域 ---
        text_frame = tk.Frame(self, padx=10, pady=10)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 识别文本
        recognized_label = tk.Label(text_frame, text="识别文本:", font=("Helvetica", 12, "bold"))
        recognized_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        self.recognized_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10,
                                                         font=("Helvetica", 14), bg="white", fg="black")
        self.recognized_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.recognized_text.config(state=tk.DISABLED)

        # 翻译文本
        translated_label = tk.Label(text_frame, text="翻译结果:", font=("Helvetica", 12, "bold"))
        translated_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        self.translated_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10,
                                                          font=("Helvetica", 14), bg="white", fg="black")
        self.translated_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.translated_text.config(state=tk.DISABLED)

    def _populate_device_dropdowns(self):
        """填充音频输入设备下拉菜单"""
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
        """填充STT和MT模型下拉菜单"""
        available_stt_models, available_mt_models = self.get_available_models_callback()

        # STT 模型
        self.stt_model_names = sorted(list(available_stt_models.keys()))
        self.stt_model_dropdown['values'] = self.stt_model_names
        if self.stt_model_names:
            from config import DEFAULT_INPUT_LANGUAGE_MODEL
            if DEFAULT_INPUT_LANGUAGE_MODEL in self.stt_model_names:
                self.selected_stt_model.set(DEFAULT_INPUT_LANGUAGE_MODEL)
            else:
                self.selected_stt_model.set(self.stt_model_names[0])

        # MT 模型
        self.mt_model_names = sorted(list(available_mt_models.keys()))
        self.mt_model_dropdown['values'] = self.mt_model_names
        if self.mt_model_names:
            from config import DEFAULT_TRANSLATION_MODEL
            if DEFAULT_TRANSLATION_MODEL in self.mt_model_names:
                self.selected_mt_model.set(DEFAULT_TRANSLATION_MODEL)
            else:
                self.selected_mt_model.set(self.mt_model_names[0])


    def _on_input_device_selected(self, event):
        print(f"选择了音频输入设备: {self.selected_input_device.get()}")

    def _on_stt_model_selected(self, event):
        print(f"选择了识别模型: {self.selected_stt_model.get()}")

    def _on_mt_model_selected(self, event):
        print(f"选择了翻译模型: {self.selected_mt_model.get()}")

    def start_translation(self):
        if self.is_running:
            return

        selected_input_device_name = self.selected_input_device.get()
        selected_input_device_id = self.input_device_ids.get(selected_input_device_name)
        selected_stt_model_name = self.selected_stt_model.get()
        selected_mt_model_name = self.selected_mt_model.get()

        if not selected_input_device_id:
            messagebox.showwarning("选择错误", "请选择一个有效的音频输入设备。")
            return
        if not selected_stt_model_name:
            messagebox.showwarning("选择错误", "请选择一个识别模型。")
            return
        if not selected_mt_model_name:
            messagebox.showwarning("选择错误", "请选择一个翻译模型。")
            return

        try:
            self.start_callback(selected_input_device_id, selected_stt_model_name, selected_mt_model_name)
            self.is_running = True
            self.status_label.config(text="状态: 监听中...", fg="blue")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL) # 启动后启用保存按钮
            self.input_device_dropdown.config(state=tk.DISABLED)
            self.stt_model_dropdown.config(state=tk.DISABLED)
            self.mt_model_dropdown.config(state=tk.DISABLED)
            self.clear_text_areas()
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动翻译：\n{e}\n请检查模型路径和依赖项。")
            self.stop_translation()

    def stop_translation(self):
        if not self.is_running:
            return

        self.stop_callback()
        self.is_running = False
        self.status_label.config(text="状态: 已停止", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED) # 停止后禁用保存按钮
        self.input_device_dropdown.config(state="readonly")
        self.stt_model_dropdown.config(state="readonly")
        self.mt_model_dropdown.config(state="readonly")

    def save_translation_to_file(self):
        """将翻译结果保存到文件"""
        translated_content = self.translated_text.get("1.0", tk.END).strip()
        if not translated_content:
            messagebox.showwarning("保存失败", "没有可保存的翻译内容。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="保存翻译结果"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(translated_content)
                messagebox.showinfo("保存成功", f"翻译结果已保存到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"保存文件失败：\n{e}")

    def append_recognized_text(self, text):
        self.recognized_text.config(state=tk.NORMAL)
        if text.startswith(" (Partial) "):
            self.recognized_text.insert(tk.END, text + "\n")
        else:
            current_content = self.recognized_text.get("1.0", tk.END)
            last_line_start = self.recognized_text.index("end-1c linestart")
            last_line_content = self.recognized_text.get(last_line_start, tk.END).strip()
            if last_line_content.startswith("(Partial)"):
                self.recognized_text.delete(last_line_start, tk.END)
            self.recognized_text.insert(tk.END, text + "\n")

        self.recognized_text.see(tk.END)
        self.recognized_text.config(state=tk.DISABLED)

    def append_translated_text(self, text):
        self.translated_text.config(state=tk.NORMAL)
        self.translated_text.insert(tk.END, text + "\n")
        self.translated_text.see(tk.END)
        self.translated_text.config(state=tk.DISABLED)

    def clear_text_areas(self):
        self.recognized_text.config(state=tk.NORMAL)
        self.recognized_text.delete(1.0, tk.END)
        self.recognized_text.config(state=tk.DISABLED)

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
