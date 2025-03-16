# 系统配置

import os
import dotenv
from pathlib import Path
from config.constants import ROOT_DIR

# 加载.env文件
dotenv.load_dotenv(ROOT_DIR / '.env')

# API配置
API_URL = os.getenv('API_URL', 'https://api.openai.com/v1')
API_KEY = os.getenv('API_KEY', '')
MODEL = os.getenv('MODEL', 'gpt-4-turbo')

# 系统配置
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4096'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))

# 获取配置
def get_config():
    """获取系统配置"""
    return {
        'api_url': API_URL,
        'api_key': API_KEY,
        'model': MODEL,
        'max_tokens': MAX_TOKENS,
        'temperature': TEMPERATURE
    }