import os
import uuid
import wave
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import time

import numpy as np
import torch
from silero_vad import load_silero_vad, VADIterator

logger = logging.getLogger(__name__)


class VAD(ABC):
    @abstractmethod
    def is_vad(self, data):
        pass

    def reset_states(self):
        pass


class SileroVAD(VAD):
    def __init__(self, config):
        logger.info("初始化 SileroVAD...")
        try:
            self.model = load_silero_vad()
            # 基本VAD参数
            self.sampling_rate = int(config.get("sampling_rate", 16000))
            self.threshold = float(config.get("threshold", 0.5))
            self.min_silence_duration_ms = int(config.get("min_silence_duration_ms", 200))
            
            # 音频处理参数
            self.channels = int(config.get("channels", 1))
            
            # 初始化VAD迭代器
            self.vad_iterator = VADIterator(
                model=self.model,
                threshold=self.threshold,
                sampling_rate=self.sampling_rate,
                min_silence_duration_ms=self.min_silence_duration_ms
            )
            
            # 状态管理
            self.is_speaking = False
            self.speech_start_time = None
            self.speech_prob_history = []
            self.SPEECH_PROB_THRESHOLD = float(config.get("speech_prob_threshold", 0.5))
            self.MIN_SPEECH_DURATION_MS = int(config.get("min_speech_duration_ms", 200))
            
            logger.info("SileroVAD 初始化成功")
        except Exception as e:
            logger.error(f"SileroVAD 初始化失败: {e}")
            raise

    @staticmethod
    def int2float(sound):
        """
        Convert int16 audio data to float32.
        """
        sound = sound.astype(np.float32) / 32768.0
        return sound

    def _process_multichannel(self, audio_data):
        """处理多声道音频数据"""
        # 将音频数据重塑为多声道格式
        audio_channels = np.frombuffer(audio_data, dtype=np.int16)
        audio_channels = audio_channels.reshape(-1, self.channels)
        
        # 对每个声道进行处理，选择信号最强的声道
        max_energy = 0
        selected_channel = 0
        for i in range(self.channels):
            energy = np.sum(np.abs(audio_channels[:, i]))
            if energy > max_energy:
                max_energy = energy
                selected_channel = i
        
        return audio_channels[:, selected_channel]

    def is_vad(self, data):
        try:
            # 处理多声道音频
            if self.channels > 1:
                audio_int16 = self._process_multichannel(data)
            else:
                audio_int16 = np.frombuffer(data, dtype=np.int16)
            
            # 转换为float32
            audio_float32 = self.int2float(audio_int16)
            audio_tensor = torch.from_numpy(audio_float32)
            
            # 使用VAD迭代器进行检测
            speech_prob = self.vad_iterator(audio_tensor)
            
            # 更新状态
            if speech_prob is not None:
                self.speech_prob_history.append(speech_prob)
                if len(self.speech_prob_history) > 10:  # 保持历史记录在合理范围
                    self.speech_prob_history.pop(0)
                
                # 使用平滑后的概率进行判断
                avg_speech_prob = sum(self.speech_prob_history) / len(self.speech_prob_history)
                
                if not self.is_speaking and avg_speech_prob > self.SPEECH_PROB_THRESHOLD:
                    self.is_speaking = True
                    self.speech_start_time = time.time()
                    return "start"
                elif self.is_speaking and avg_speech_prob < self.SPEECH_PROB_THRESHOLD:
                    if time.time() - self.speech_start_time > self.MIN_SPEECH_DURATION_MS / 1000:
                        self.is_speaking = False
                        self.speech_start_time = None
                        return "end"
            
            return None
            
        except Exception as e:
            logger.error(f"Error in VAD processing: {e}")
            return None

    def reset_states(self):
        try:
            self.vad_iterator.reset_states()
            self.is_speaking = False
            self.speech_start_time = None
            self.speech_prob_history = []
            logger.debug("VAD states reset.")
        except Exception as e:
            logger.error(f"Error resetting VAD states: {e}")


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")
