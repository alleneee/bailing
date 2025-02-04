import os
import uuid
import wave
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import numpy as np

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess


logger = logging.getLogger(__name__)


class ASR(ABC):
    @staticmethod
    def _save_audio_to_file(audio_data, file_path):
        """将音频数据保存为WAV文件"""
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b''.join(audio_data))
            logger.info(f"ASR识别文件录音保存到：{file_path}")
        except Exception as e:
            logger.error(f"保存音频文件时发生错误: {e}")
            raise

    @abstractmethod
    def recognizer(self, stream_in_audio):
        """处理输入音频流并返回识别的文本，子类必须实现"""
        pass


class FunASR(ASR):
    def __init__(self, config):
        self.model_dir = config.get("model_dir")
        self.output_dir = config.get("output_file")
        self.use_streaming = config.get("use_streaming", True)  # 是否使用流式处理
        self.language = config.get("language", "auto")  # 语言设置
        self.batch_size = config.get("batch_size", 60)  # 批处理大小
        self.max_cache_size = config.get("max_cache_size", 100)  # 缓存大小
        self.cache = {}  # 用于流式处理的缓存

        # 初始化模型
        self.model = AutoModel(
            model=self.model_dir,
            vad_kwargs={
                "max_single_segment_time": config.get("max_segment_time", 30000),
                "min_duration_on": config.get("min_duration_on", 200),
                "min_duration_off": config.get("min_duration_off", 200)
            },
            disable_update=True,
            hub="hf",
            use_streaming=self.use_streaming
            # device="cuda:0",  # 如果有GPU，可以解开这行并指定设备
        )

        # 预热模型
        self._warmup_model()

    def _warmup_model(self):
        """预热模型，提高首次识别速度"""
        try:
            logger.info("正在预热ASR模型...")
            dummy_audio = np.zeros(16000, dtype=np.int16)  # 1秒的空白音频
            dummy_file = os.path.join(self.output_dir, "warmup.wav")
            self._save_audio_to_file([dummy_audio.tobytes()], dummy_file)
            self.model.generate(
                input=dummy_file,
                cache={},
                language=self.language,
                use_itn=True,
                batch_size_s=self.batch_size
            )
            os.remove(dummy_file)
            logger.info("ASR模型预热完成")
        except Exception as e:
            logger.error(f"模型预热失败: {e}")

    def _clean_cache(self):
        """清理过期的缓存"""
        if len(self.cache) > self.max_cache_size:
            # 删除最旧的缓存
            oldest_key = min(self.cache.keys())
            del self.cache[oldest_key]

    def recognizer(self, stream_in_audio):
        try:
            # 生成唯一的会话ID
            session_id = str(uuid.uuid4())
            tmpfile = os.path.join(self.output_dir, f"asr-{datetime.now().date()}@{session_id}.wav")
            self._save_audio_to_file(stream_in_audio, tmpfile)

            # 使用流式处理
            if self.use_streaming:
                self._clean_cache()
                self.cache[session_id] = self.cache.get(session_id, {})
                
                res = self.model.generate(
                    input=tmpfile,
                    cache=self.cache[session_id],
                    language=self.language,
                    use_itn=True,
                    batch_size_s=self.batch_size,
                )
            else:
                # 非流式处理
                res = self.model.generate(
                    input=tmpfile,
                    cache={},
                    language=self.language,
                    use_itn=True,
                    batch_size_s=self.batch_size,
                )

            if res and len(res) > 0:
                text = rich_transcription_postprocess(res[0]["text"])
                logger.info(f"识别文本: {text}")
                return text, tmpfile
            else:
                logger.warning("ASR未识别到有效文本")
                return "", tmpfile

        except Exception as e:
            logger.error(f"ASR识别过程中发生错误: {e}")
            return None, None

    def reset_cache(self, session_id=None):
        """重置指定会话或所有会话的缓存"""
        if session_id:
            if session_id in self.cache:
                del self.cache[session_id]
        else:
            self.cache.clear()


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")