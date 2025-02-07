# Bailing智能对话助手

一个基于FastAPI的智能对话系统，集成了文本对话和语音合成功能。

## 主要功能

- 智能对话：基于Dify API实现的智能对话功能
- 语音识别：
  - 支持实时语音转文字
  - 高精度中文语音识别
  - 噪音抑制和环境适应
  - 无需点击的语音唤醒
- 语音合成：集成海螺API的文本转语音功能
- WebSocket实时通信：支持实时对话交互
- 跨域支持：支持跨域请求，方便前端集成
- 虚拟数字人集成：
  - 支持3D虚拟形象展示
  - 面部表情和动作同步
  - 多角色切换功能
  - 实时语音驱动动画

## 技术栈

- FastAPI：高性能的Python Web框架
- WebSocket：实现实时双向通信
- Dify API：提供智能对话能力
- 海螺API：提供语音合成服务
- FunASR+silero-vad：本地语音识别引擎
- WebRTC：浏览器实时语音采集
- Three.js：3D虚拟形象渲染引擎（待完善）
- Live2D/Unity：虚拟形象动画系统（待完善）

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd bailing
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置API密钥和模型
- 在`run_fastapi.py`中配置Dify API密钥和海螺API密钥
- 根据需要修改配置文件`config/config.yaml`
- 下载Whisper语音识别模型（可选large或medium模型）

## 技术实现

### 语音转文字使用的技术

1. 前端技术
- WebRTC: 实现浏览器端的实时语音采集
- MediaRecorder API: 处理音频流的录制和传输
- WebSocket: 实现客户端和服务器的实时通信

2. 后端技术
- FastAPI: 提供高性能的Web服务
- PyAudio: 音频流处理和噪音消除
- Whisper: OpenAI的语音识别模型
- WebRTC VAD: 语音活动检测，减少无效处理

3. 优化技术
- WebAssembly: 加速浏览器端的语音处理
- 流式处理: 实现实时的音频分块传输和处理
- 并发处理: 使用asyncio进行异步IO操作

## 使用方法

1. 启动FastAPI服务器
```bash
python run_fastapi.py
```

2. 启动主程序
```bash
python main.py --config_path config/config.yaml
```

## 项目结构

- `run_fastapi.py`: FastAPI服务器入口
- `main.py`: 主程序入口
- `config/`: 配置文件目录
- `bailing/`: 核心功能模块
- `plugins/`: 插件目录
- `frontend/`: 前端代码
- `templates/`: 模板文件

## 注意事项

- 使用前请确保已正确配置所有必要的API密钥
- 在生产环境中请适当配置CORS和安全设置
- 确保系统已安装所有必要的Python依赖
- 虚拟数字人功能需要：
  - 较高的GPU性能支持
  - WebGL兼容的现代浏览器
  - 足够的网络带宽保证实时交互
- 语音识别功能需要：
  - 支持WebRTC的现代浏览器
  - 高质量麦克风设备
  - 充足的CPU性能（用于本地语音识别）
- 语音识别性能优化：
  - 考虑使用WebAssembly加速语音处理
  - 适当调整音频采样率和缓冲区大小
  - 使用VAD技术减少不必要的处理

## License

本项目采用 MIT 许可证