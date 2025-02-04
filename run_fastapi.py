from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import aiohttp
from typing import List
import logging
from fastapi.responses import StreamingResponse
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dify API配置
DIFY_API_KEY = "app-ETj32anudzJTI01qLQJoE8H5"  # 应用ID
DIFY_API_ENDPOINT = "http://localhost"  # Docker中的Dify实例地址

# TTS配置
TTS_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLkvZXml60iLCJVc2VyTmFtZSI6IuS9leaXrSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxODg1MjMyMzg0MDY5MDkxNzAzIiwiUGhvbmUiOiIxMzA0MTE5OTE5NiIsIkdyb3VwSUQiOiIxODg1MjMyMzg0MDYwNzAzMDk1IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDItMDQgMDM6MTU6MzYiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.hwLeQrAlRmxpfasv_rHCIvSHCtdZ8rUMBoqdn76OG0-aE7A23UuNpGsh7fzUoulnEFhGEU7dA5Y7fH3qXTrzR2aVtuFi80I9CVTbJHMrOekCvQx926rRGc3mNF6gxLkXBRzowmkVmXtO2hb4KvrVVb_MmAztSLGbHWmjPcUZlcVTLHSavuDRKwQLlIg00NuWorC2TxBvvE5v4HplLq_xq6TqnAMSahXejb79QsEDQCYyzRcSTgDE5ogYdDYd5Z0TFkOT4OXqbzGm5N9WQRNiJFwvYEolmokz5_Y_pYMzHR2KIgeKU2gl0x2mDDwIdUXCKPo2fNBuDV3rk8rlOw6RoA"  # 海螺API密钥
GROUP_ID = "1885232384060703095"  # 从API密钥中提取的GroupId
TTS_API_ENDPOINT = f"https://api.minimax.chat/v1/t2a_v2?GroupId={GROUP_ID}"  # 海螺T2A V2 API地址

# 存储活动的WebSocket连接
active_connections: List[WebSocket] = []

async def get_dify_response(message: str) -> str:
    """调用Dify API获取回答"""
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0"
    }
    
    # 使用chat-messages接口
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "user-123"
    }
    
    logger.info(f"发送到Dify的请求: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"{DIFY_API_ENDPOINT}/v1/chat-messages"
            logger.info(f"调用API URL: {api_url}")
            async with session.post(api_url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"Dify API响应状态码: {response.status}")
                logger.info(f"Dify API响应内容: {response_text}")
                
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        answer = result.get("answer", "抱歉，无法获取回答。")
                        logger.info(f"成功获取回答: {answer}")
                        return answer
                    except json.JSONDecodeError as e:
                        logger.error(f"解析响应JSON时出错: {str(e)}")
                        return "抱歉，服务器返回了无效的响应。"
                else:
                    error_message = f"Dify API错误: 状态码 {response.status}, 响应: {response_text}"
                    logger.error(error_message)
                    return f"抱歉，服务器返回了错误: {error_message}"
    except Exception as e:
        error_message = f"调用Dify API时出错: {str(e)}"
        logger.error(error_message)
        return f"抱歉，调用AI服务时出错: {error_message}"

async def handle_message(websocket: WebSocket, message: str):
    """处理接收到的消息并返回响应"""
    try:
        # 解析消息
        data = json.loads(message)
        logger.info(f"收到WebSocket消息: {json.dumps(data, ensure_ascii=False)}")
        
        if data["role"] == "user":
            # 获取AI回答
            ai_response = await get_dify_response(data["content"])
            logger.info(f"AI回答: {ai_response}")
            
            # 创建助手响应
            response = {
                "role": "assistant",
                "content": ai_response
            }
            # 发送响应
            await websocket.send_json(response)
            logger.info(f"已发送响应: {json.dumps(response, ensure_ascii=False)}")
    except json.JSONDecodeError as e:
        logger.error(f"无效的JSON消息: {message}, 错误: {str(e)}")
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("新的WebSocket连接已建立")
    
    try:
        while True:
            # 接收消息
            message = await websocket.receive_text()
            # 处理消息
            await handle_message(websocket, message)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        # 连接关闭时清理
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info("WebSocket连接已关闭")

@app.post("/tts")
async def text_to_speech(request: dict):
    """将文本转换为语音"""
    try:
        text = request.get("text", "")
        if not text:
            return {"error": "文本不能为空"}

        headers = {
            "Authorization": f"Bearer {TTS_API_KEY}",
            "Content-Type": "application/json",
            "accept": "application/json, text/plain, */*"
        }
        
        data = {
            "model": "speech-01-turbo",
            "text": text,
            "stream": False,  # 不使用流式响应
            "voice_setting": {
                "voice_id": "male-qn-qingse",  # 青色男声
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }

        logger.info(f"发送TTS请求: {json.dumps(data, ensure_ascii=False)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(TTS_API_ENDPOINT, headers=headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if "data" in response_json and "audio" in response_json["data"]:
                        # 解码base64音频数据
                        audio_hex = response_json["data"]["audio"]
                        audio_data = bytes.fromhex(audio_hex)
                        return StreamingResponse(
                            io.BytesIO(audio_data),
                            media_type="audio/mpeg"
                        )
                    else:
                        error_text = "响应中没有音频数据"
                        logger.error(error_text)
                        return {"error": error_text}
                else:
                    error_text = await response.text()
                    logger.error(f"TTS API错误: {response.status}, {error_text}")
                    return {"error": f"TTS服务错误: {response.status}"}
    except Exception as e:
        logger.error(f"TTS处理错误: {str(e)}")
        return {"error": f"TTS处理失败: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    logger.info("启动FastAPI服务器...")
    uvicorn.run(app, host="127.0.0.1", port=8000) 