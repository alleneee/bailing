import logging
from typing import Any, Dict, List, Optional, Iterator
from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import QianfanLLMEndpoint
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.llms import SparkLLM
from langchain_community.llms import BaichuanLLM

logger = logging.getLogger(__name__)

class BaseLLM(BaseChatModel, ABC):
    """基础LLM类，继承自LangChain的BaseChatModel"""
    
    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """流式聊天"""
        pass

class OpenAILLM(BaseLLM):
    """OpenAI LLM实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = ChatOpenAI(
            model_name=config.get("model_name"),
            openai_api_key=config.get("api_key"),
            openai_api_base=config.get("url"),
            streaming=True
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs)
            for chunk in response:
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs])
        return response

class QianfanLLM(BaseLLM):
    """百度千帆(文心一言)实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = QianfanLLMEndpoint(
            streaming=True,
            qianfan_ak=config.get("ak"),
            qianfan_sk=config.get("sk")
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs[-1].get("content"))
            for chunk in response:
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs[-1].content])
        return ChatResult(generations=[ChatGeneration(message=response.generations[0][0])])

class ZhipuAILLM(BaseLLM):
    """智谱AI(ChatGLM)实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = ChatZhipuAI(
            model=config.get("model", "glm-4"),
            api_key=config.get("api_key"),
            streaming=True
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs)
            for chunk in response:
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs])
        return response

class SparkLLM(BaseLLM):
    """讯飞星火实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = SparkLLM(
            app_id=config.get("app_id"),
            api_key=config.get("api_key"),
            api_secret=config.get("api_secret")
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs[-1].get("content"))
            for chunk in response:
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs[-1].content])
        return ChatResult(generations=[ChatGeneration(message=response.generations[0][0])])

class BaichuanLLM(BaseLLM):
    """百川实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = BaichuanLLM(
            api_key=config.get("api_key")
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs[-1].get("content"))
            for chunk in response:
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs[-1].content])
        return ChatResult(generations=[ChatGeneration(message=response.generations[0][0])])

class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = ChatOpenAI(
            model_name=config.get("model_name", "deepseek-chat"),
            openai_api_key=config.get("api_key"),
            openai_api_base=config.get("url", "https://api.deepseek.com/v1"),
            streaming=True,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
            model_kwargs={
                "stop": config.get("stop_sequences", []),
                "top_p": config.get("top_p", 0.9),
            }
        )
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        try:
            message_objs = [
                self._convert_message_to_langchain(msg) for msg in messages
            ]
            response = self.client.stream(message_objs)
            for chunk in response:
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            raise

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_objs = [msg for msg in messages]
        response = self.client.generate([message_objs])
        return response

def create_llm(provider: str, config: Dict[str, Any]) -> BaseLLM:
    """
    LLM工厂方法
    
    Args:
        provider: LLM提供商名称
        config: 配置信息
    
    Returns:
        LLM实例
    """
    providers = {
        "OpenAILLM": OpenAILLM,
        "QianfanLLM": QianfanLLM,
        "ZhipuAILLM": ZhipuAILLM,
        "SparkLLM": SparkLLM,
        "BaichuanLLM": BaichuanLLM,
        "DeepSeekLLM": DeepSeekLLM
    }
    
    if provider not in providers:
        raise ValueError(f"不支持的LLM提供商: {provider}")
    
    return providers[provider](config)

def create_instance(class_name, config):
    """
    创建LLM实例
    
    Args:
        class_name: LLM类名
        config: 配置信息
    
    Returns:
        LLM实例
    """
    return create_llm(class_name, config)
