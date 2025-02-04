from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
import logging

logger = logging.getLogger(__name__)

prompt_template = """请根据以下上下文回答最后的问题。如果你不知道答案，请直接说不知道，切勿编造答案。回答应简洁明了，最多使用三句话，确保直接针对问题，并鼓励提问者提出更多问题。

{context}

问题：{question}

有帮助的答案："""

class DifyLLMWrapper:
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def __call__(self, prompt):
        try:
            response = requests.post(
                f"{self.endpoint}/chat-messages",
                headers=self.headers,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "")
            else:
                logger.error(f"Dify API请求失败: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"调用Dify API时出错: {e}")
            return ""

class Rag:
    _instance = None

    def __new__(cls, config: dict=None):
        if cls._instance is None:
            cls._instance = super(Rag, cls).__new__(cls)
            cls._instance.init(config)  # 初始化实例属性
        return cls._instance

    def init(self, config: dict):
        self.doc_path = config.get("doc_path")
        
        # 使用Dify配置
        dify_config = config.get("dify", {})
        self.api_key = dify_config.get("api_key")
        self.endpoint = dify_config.get("endpoint", "https://api.dify.ai/v1")
        
        # 设置API请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def query(self, query):
        try:
            # 使用Dify的Chat Completion API
            response = requests.post(
                f"{self.endpoint}/chat-messages",
                headers=self.headers,
                json={
                    "messages": [{"role": "user", "content": query}],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "")
            else:
                logger.error(f"Dify API请求失败: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"调用Dify API时出错: {e}")
            return ""


if __name__ == "__main__":
    config = {""}
