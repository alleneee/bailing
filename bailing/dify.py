import json
import logging
import requests
from typing import Optional, Dict, Generator, Any

logger = logging.getLogger(__name__)

class DifyLLM:
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.dify.ai/v1",
        conversation_id: Optional[str] = None
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.conversation_id = conversation_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> requests.Response:
        """发送请求到Dify API"""
        url = f"{self.endpoint}/{endpoint}"
        try:
            response = requests.post(url, json=payload, headers=self.headers, stream=stream)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API请求失败: {e}")
            raise

    def chat_completion(
        self,
        messages: list,
        stream: bool = False,
        user: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        调用Dify Chat Completion API
        
        Args:
            messages: 对话消息列表
            stream: 是否使用流式响应
            user: 用户标识
            **kwargs: 其他参数
        
        Returns:
            如果stream=False，返回完整响应
            如果stream=True，返回响应生成器
        """
        payload = {
            "messages": messages,
            "conversation_id": self.conversation_id,
            "user": user,
            **kwargs
        }

        if stream:
            response = self._make_request("chat-messages", payload, stream=True)
            return self._handle_stream_response(response)
        else:
            response = self._make_request("chat-messages", payload)
            return response.json()

    def _handle_stream_response(
        self,
        response: requests.Response
    ) -> Generator[Dict[str, Any], None, None]:
        """处理流式响应"""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    yield data
                except json.JSONDecodeError as e:
                    logger.error(f"解析流式响应失败: {e}")
                    continue

    def completion(
        self,
        prompt: str,
        stream: bool = False,
        user: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        调用Dify Completion API
        
        Args:
            prompt: 提示文本
            stream: 是否使用流式响应
            user: 用户标识
            **kwargs: 其他参数
            
        Returns:
            如果stream=False，返回完整响应
            如果stream=True，返回响应生成器
        """
        payload = {
            "prompt": prompt,
            "user": user,
            **kwargs
        }

        if stream:
            response = self._make_request("completion-messages", payload, stream=True)
            return self._handle_stream_response(response)
        else:
            response = self._make_request("completion-messages", payload)
            return response.json()

    def set_conversation_id(self, conversation_id: str):
        """设置会话ID"""
        self.conversation_id = conversation_id

    def response(self, messages: list) -> Generator[str, None, None]:
        """
        处理普通对话
        
        Args:
            messages: 对话消息列表
            
        Returns:
            生成器,产生回复内容
        """
        response = self.chat_completion(messages, stream=True)
        for chunk in response:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    def response_call(self, messages: list, functions_call: list = None) -> Generator[tuple[Optional[str], Optional[list]], None, None]:
        """
        处理带有函数调用的对话
        
        Args:
            messages: 对话消息列表
            functions_call: 可用的函数列表
            
        Returns:
            生成器,产生(content, tool_calls)元组
        """
        # 添加函数定义到请求
        kwargs = {}
        if functions_call:
            kwargs["tools"] = functions_call
            kwargs["tool_choice"] = "auto"
        
        response = self.chat_completion(messages, stream=True, **kwargs)
        for chunk in response:
            content = None
            tool_calls = None
            
            if "message" in chunk:
                if "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                if "tool_calls" in chunk["message"]:
                    tool_calls = chunk["message"]["tool_calls"]
            
            yield content, tool_calls 