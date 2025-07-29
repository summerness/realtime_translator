# audio_io.py
import sounddevice as sd
import numpy as np
from config import SAMPLE_RATE, BLOCK_SIZE, CHANNELS

class AudioRecorder:
    def __init__(self, device_id=None, sample_rate=SAMPLE_RATE, block_size=BLOCK_SIZE, channels=CHANNELS):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.device_id = device_id
        self.stream = None
        self._buffer = []

    @staticmethod
    def list_audio_input_devices():
        """列出所有可用的音频输入设备"""
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({'id': i, 'name': device['name'], 'hostapi': sd.query_hostapis(device['hostapi'])['name']})
        return input_devices

    @staticmethod
    def list_audio_output_devices():
        """列出所有可用的音频输出设备"""
        devices = sd.query_devices()
        output_devices = []
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                output_devices.append({'id': i, 'name': device['name'], 'hostapi': sd.query_hostapis(device['hostapi'])['name']})
        return output_devices

    def start_recording(self):
        """开始录音流"""
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=self.channels,
                dtype='int16',
                callback=self._audio_callback,
                device=self.device_id
            )
            self.stream.start()
            current_device_info = sd.query_devices(self.device_id) if self.device_id is not None else sd.query_devices(sd.default.device[0])
            print(f"开始录音，设备: {current_device_info['name']}, 采样率: {self.sample_rate} Hz, 块大小: {self.block_size} 采样")
        except Exception as e:
            print(f"启动录音失败: {e}")
            self.stream = None
            raise

    def _audio_callback(self, indata, frames, time, status):
        """ sounddevice 回调函数，每当有音频数据可用时被调用 """
        if status:
            print(f"录音状态警告: {status}")
        self._buffer.append(bytes(indata))

    def get_audio_chunk(self):
        """获取并清空缓冲区中的一个音频块"""
        if self._buffer:
            chunk = b''.join(self._buffer)
            self._buffer = []
            return chunk
        return None

    def stop_recording(self):
        """停止录音流"""
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
            print("录音已停止。")
        self.stream = None

# 示例使用 (在 main.py 中调用)
if __name__ == "__main__":
    print("可用音频输入设备:")
    input_devices = AudioRecorder.list_audio_input_devices()
    for dev in input_devices:
        print(f"  ID: {dev['id']}, 名称: {dev['name']}, API: {dev['hostapi']}")

    print("\n可用音频输出设备:")
    output_devices = AudioRecorder.list_audio_output_devices()
    for dev in output_devices:
        print(f"  ID: {dev['id']}, 名称: {dev['name']}, API: {dev['hostapi']}")

    if input_devices:
        recorder = AudioRecorder(device_id=input_devices[0]['id'])
        recorder.start_recording()
        import time
        try:
            while True:
                chunk = recorder.get_audio_chunk()
                if chunk:
                    print(f"捕获到音频块大小: {len(chunk)} 字节")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("用户中断。")
        finally:
            recorder.stop_recording()
    else:
        print("未找到任何音频输入设备。")