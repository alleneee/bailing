import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from bailing.dify import DifyLLM
from bailing.config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Bailing Chat",
    description="A chat application built with FastAPI"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="server/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="server/templates")

# 配置Dify
dify_config = config.get("dify", {})
dify_llm = DifyLLM(
    api_key=dify_config.get("api_key"),
    endpoint=dify_config.get("endpoint", "https://api.dify.ai/v1")
)

# 消息模型
class Message(BaseModel):
    role: str
    content: str
    time: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    stream: bool = False
    user: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.dialogue_history: List[Dict] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
    
    def add_message(self, message: dict):
        message["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.dialogue_history.append(message)

manager = ConnectionManager()

# 路由
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # 如果是用户消息，则调用Dify获取回复
                if message.get("role") == "user":
                    dify_response = dify_llm.chat_completion(
                        messages=[{"role": "user", "content": message["content"]}],
                        stream=False
                    )
                    # 添加用户消息
                    manager.add_message(message)
                    # 添加助手回复
                    assistant_message = {
                        "role": "assistant",
                        "content": dify_response["answer"],
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    manager.add_message(assistant_message)
                    # 广播两条消息
                    await manager.broadcast(message)
                    await manager.broadcast(assistant_message)
                else:
                    manager.add_message(message)
                    await manager.broadcast(message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/message")
async def add_message(message: Message):
    message_dict = message.dict()
    if not message_dict.get("time"):
        message_dict["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manager.add_message(message_dict)
    await manager.broadcast(message_dict)
    return {"status": "success"}

@app.get("/dialogue")
async def get_dialogue():
    return {"dialogue": manager.dialogue_history}

@app.post("/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 合并配置
        kwargs = {
            "temperature": request.temperature or dify_config.get("settings", {}).get("temperature"),
            "top_p": request.top_p or dify_config.get("settings", {}).get("top_p"),
            "max_tokens": request.max_tokens or dify_config.get("settings", {}).get("max_tokens")
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        if request.stream:
            return StreamingResponse(
                dify_llm.chat_completion(
                    messages=request.messages,
                    stream=True,
                    user=request.user or dify_config.get("default_user"),
                    **kwargs
                ),
                media_type="text/event-stream"
            )
        else:
            response = dify_llm.chat_completion(
                messages=request.messages,
                stream=False,
                user=request.user or dify_config.get("default_user"),
                **kwargs
            )
            return response
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/completion")
async def completion(
    prompt: str,
    stream: bool = False,
    user: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """处理单次补全请求"""
    try:
        # 合并配置
        kwargs = {
            "temperature": temperature or dify_config.get("settings", {}).get("temperature"),
            "top_p": top_p or dify_config.get("settings", {}).get("top_p"),
            "max_tokens": max_tokens or dify_config.get("settings", {}).get("max_tokens")
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        if stream:
            return StreamingResponse(
                dify_llm.completion(
                    prompt=prompt,
                    stream=True,
                    user=user or dify_config.get("default_user"),
                    **kwargs
                ),
                media_type="text/event-stream"
            )
        else:
            response = dify_llm.completion(
                prompt=prompt,
                stream=False,
                user=user or dify_config.get("default_user"),
                **kwargs
            )
            return response
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    ) 