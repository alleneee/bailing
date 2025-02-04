import asyncio
import logging
import os
import subprocess
import time
import uuid
import wave
from abc import ABC, ABCMeta, abstractmethod
from datetime import datetime
import pyaudio
from pydub import AudioSegment
from gtts import gTTS
import edge_tts
import ChatTTS
import torch
import torchaudio
import aiohttp
import json
import requests

logger = logging.getLogger(__name__)


class AbstractTTS(ABC):
    __metaclass__ = ABCMeta

    @abstractmethod
    def to_tts(self, text):
        pass


class GTTS(AbstractTTS):
    def __init__(self, config):
        self.output_file = config.get("output_file")
        self.lang = config.get("lang")

    def _generate_filename(self, extension=".aiff"):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}")

    def _log_execution_time(self, start_time):
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"执行时间: {execution_time:.2f} 秒")

    def to_tts(self, text):
        tmpfile = self._generate_filename(".aiff")
        try:
            start_time = time.time()
            tts = gTTS(text=text, lang=self.lang)
            tts.save(tmpfile)
            self._log_execution_time(start_time)
            return tmpfile
        except Exception as e:
            logger.debug(f"生成TTS文件失败: {e}")
            return None


class MacTTS(AbstractTTS):
    """
    macOS 系统自带的TTS
    voice: say -v ? 可以打印所有语音
    """

    def __init__(self, config):
        super().__init__()
        self.voice = config.get("voice")
        self.output_file = config.get("output_file")

    def _generate_filename(self, extension=".aiff"):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}")

    def _log_execution_time(self, start_time):
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"执行时间: {execution_time:.2f} 秒")

    def to_tts(self, phrase):
        logger.debug(f"正在转换的tts：{phrase}")
        tmpfile = self._generate_filename(".aiff")
        try:
            start_time = time.time()
            res = subprocess.run(
                ["say", "-v", self.voice, "-o", tmpfile, phrase],
                shell=False,
                universal_newlines=True,
            )
            self._log_execution_time(start_time)
            if res.returncode == 0:
                return tmpfile
            else:
                logger.info("TTS 生成失败")
                return None
        except Exception as e:
            logger.info(f"执行TTS失败: {e}")
            return None


class EdgeTTS(AbstractTTS):
    def __init__(self, config):
        self.voice = config.get("voice")
        self.output_file = config.get("output_file")
        self.stream_mode = config.get("stream_mode", True)  # 默认启用流式模式

    def _generate_filename(self, extension=".mp3"):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}")

    async def _stream_tts(self, text, output_file):
        communicate = edge_tts.Communicate(text, self.voice)
        try:
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
            return output_file
        except Exception as e:
            logger.error(f"流式TTS生成失败: {e}")
            return None

    def to_tts(self, text):
        if not text:
            return None
            
        tmpfile = self._generate_filename()
        try:
            start_time = time.time()
            if self.stream_mode:
                # 使用流式模式
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._stream_tts(text, tmpfile))
                loop.close()
            else:
                # 使用非流式模式
                communicate = edge_tts.Communicate(text, self.voice)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(communicate.save(tmpfile))
                loop.close()

            end_time = time.time()
            logger.debug(f"TTS执行时间: {end_time - start_time:.2f} 秒")
            return tmpfile
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            return None


class CHATTTS(AbstractTTS):
    def __init__(self, config):
        self.output_file = config.get("output_file", ".")
        self.chat = ChatTTS.Chat()
        self.chat.load(compile=False)  # Set to True for better performance
        self.rand_spk = self.chat.sample_random_speaker()

    def _generate_filename(self, extension=".wav"):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}")

    def _log_execution_time(self, start_time):
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Execution Time: {execution_time:.2f} seconds")

    def to_tts(self, text):
        tmpfile = self._generate_filename(".wav")
        start_time = time.time()
        try:
            params_infer_code = ChatTTS.Chat.InferCodeParams(
                spk_emb=self.rand_spk,  # add sampled speaker
                temperature=.3,  # using custom temperature
                top_P=0.7,  # top P decode
                top_K=20,  # top K decode
            )
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt='[oral_2][laugh_0][break_6]',
            )
            wavs = self.chat.infer(
                [text],
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
            )
            try:
                torchaudio.save(tmpfile, torch.from_numpy(wavs[0]).unsqueeze(0), 24000)
            except:
                torchaudio.save(tmpfile, torch.from_numpy(wavs[0]), 24000)
            self._log_execution_time(start_time)
            return tmpfile
        except Exception as e:
            logger.error(f"Failed to generate TTS file: {e}")
            return None


class MinimaxTTS(AbstractTTS):
    """海螺TTS实现"""
    def __init__(self, config):
        self.output_file = config.get("output_file")
        self.api_key = config.get("api_key")
        self.group_id = config.get("group_id")
        self.model = config.get("model", "speech-01-turbo")
        self.stream_mode = config.get("stream_mode", True)
        self.voice_id = config.get("voice_id", "male-qn-qingse")
        self.api_url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
        
        # 音频设置
        self.audio_setting = {
            "sample_rate": config.get("sample_rate", 32000),
            "bitrate": config.get("bitrate", 128000),
            "format": config.get("format", "mp3"),
            "channel": config.get("channel", 1)
        }
        
        # 语音设置
        self.voice_setting = {
            "voice_id": self.voice_id,
            "speed": config.get("speed", 1.0),
            "vol": config.get("vol", 1.0),
            "pitch": config.get("pitch", 0),
            "emotion": config.get("emotion", "normal")
        }
        
        # 验证必要的配置
        if not self.api_key:
            raise ValueError("Minimax TTS requires api_key")
        if not self.group_id:
            raise ValueError("Minimax TTS requires group_id")

    def _generate_filename(self, extension=".mp3"):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}")

    async def _stream_tts(self, text, output_file):
        """流式生成TTS音频"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": self.voice_setting,
            "audio_setting": self.audio_setting
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=data, headers=headers) as response:
                    with open(output_file, "wb") as f:
                        async for chunk in response.content.iter_chunked(1024):
                            if chunk.startswith(b'data:'):
                                try:
                                    data = json.loads(chunk[5:])
                                    if "data" in data and "audio" in data["data"]:
                                        audio_data = bytes.fromhex(data["data"]["audio"])
                                        f.write(audio_data)
                                except json.JSONDecodeError:
                                    continue
            return output_file
        except Exception as e:
            logger.error(f"流式TTS生成失败: {e}")
            return None

    def _non_stream_tts(self, text, output_file):
        """非流式生成TTS音频"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "text": text,
            "stream": False,
            "voice_setting": self.voice_setting,
            "audio_setting": self.audio_setting
        }
        
        try:
            response = requests.post(self.api_url, json=data, headers=headers)
            response_data = response.json()
            
            if response_data.get("base_resp", {}).get("status_code") == 0:
                audio_data = bytes.fromhex(response_data["data"]["audio"])
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                return output_file
            else:
                logger.error(f"TTS API返回错误: {response_data.get('base_resp', {}).get('status_msg')}")
                return None
        except Exception as e:
            logger.error(f"非流式TTS生成失败: {e}")
            return None

    def to_tts(self, text):
        """生成TTS音频"""
        if not text:
            return None
            
        tmpfile = self._generate_filename(f".{self.audio_setting['format']}")
        try:
            start_time = time.time()
            
            if self.stream_mode:
                # 使用流式模式
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._stream_tts(text, tmpfile))
                loop.close()
            else:
                # 使用非流式模式
                result = self._non_stream_tts(text, tmpfile)

            end_time = time.time()
            logger.debug(f"TTS执行时间: {end_time - start_time:.2f} 秒")
            return result
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            return None


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")
