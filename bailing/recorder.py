import time
from abc import ABC, abstractmethod
import threading
import queue
import logging
import pyaudio

logger = logging.getLogger(__name__)


class AbstractRecorder(ABC):
    @abstractmethod
    def start_recording(self, audio_queue: queue.Queue):
        pass

    @abstractmethod
    def stop_recording(self):
        pass


class RecorderPyAudio(AbstractRecorder):
    def __init__(self, config=None):
        self.CHUNK = 480  # 减小缓冲区大小，提高响应速度
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.recording = False
        self.frames = []
        self.p = None
        self.stream = None
        if config:
            self.CHUNK = config.get('chunk', self.CHUNK)
            self.CHANNELS = config.get('channels', self.CHANNELS)
            self.RATE = config.get('rate', self.RATE)

    def start_recording(self, audio_queue: queue.Queue):
        """开始录音"""
        self.recording = True
        self.p = pyaudio.PyAudio()
        
        def callback(in_data, frame_count, time_info, status):
            if self.recording:
                audio_queue.put(in_data)
            return (in_data, pyaudio.paContinue)

        # 使用回调方式实现流式处理
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=callback
        )
        
        self.stream.start_stream()
        logger.info("开始录音...")

    def stop_recording(self):
        """停止录音"""
        if self.recording:
            self.recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
            logger.info("录音已停止。")

    def __del__(self):
        # Ensure resources are cleaned up on object deletion
        self.stop_recording()


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")


if __name__ == "__main__":
    audio_queue = queue.Queue()
    recorderPyAudio = RecorderPyAudio()
    recorderPyAudio.start_recording()
    time.sleep(10)

