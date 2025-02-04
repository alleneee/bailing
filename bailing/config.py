import os
import yaml
from typing import Dict, Any

def load_config(config_path: str = "config") -> Dict[str, Any]:
    """加载配置文件"""
    config = {}
    
    # 加载所有yaml配置文件
    for file in os.listdir(config_path):
        if file.endswith(".yaml"):
            file_path = os.path.join(config_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                config.update(yaml.safe_load(f))
    
    # 环境变量覆盖
    if "DIFY_API_KEY" in os.environ:
        config["dify"]["api_key"] = os.environ["DIFY_API_KEY"]
    if "DIFY_ENDPOINT" in os.environ:
        config["dify"]["endpoint"] = os.environ["DIFY_ENDPOINT"]
    
    return config

# 全局配置对象
config = load_config() 