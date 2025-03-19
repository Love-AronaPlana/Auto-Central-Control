"""ASN基础模块

该模块负责：
1. 提供系统基础配置
2. 初始化必要的系统组件
3. 提供系统级的工具函数
"""

import argparse
import datetime
import json
import logging
import os
import sys
from typing import Dict, Any
import json

from ASN.config import get_llm_config
llm_config = get_llm_config()

from ASN.workflow import run_workflow

# 配置日志
logger = logging.getLogger(__name__)

class ASN:
    """ASN系统基础类"""
    
    def __init__(self):
        """初始化ASN系统基础组件"""
        logger.info("初始化ASN系统基础组件")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保系统必要的目录存在"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dirs = ['logs', 'memory', 'examples']
        
        for dir_name in dirs:
            dir_path = os.path.join(base_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"创建系统目录: {dir_path}")

# 创建全局ASN实例
_asn_instance = None

def get_asn_instance() -> ASN:
    """获取ASN系统实例
    
    Returns:
        ASN实例
    """
    global _asn_instance
    
    if _asn_instance is None:
        _asn_instance = ASN()
    
    return _asn_instance

def run_asn(user_input: str) -> Dict[str, Any]:
    """运行ASN系统（向后兼容的接口）
    
    Args:
        user_input: 用户输入
        
    Returns:
        运行结果字典
    """
    # 确保系统已初始化
    get_asn_instance()
    
    # 调用工作流程
    return run_workflow(user_input)

def configure_logging():
    """配置系统日志"""
    logging.basicConfig(
        level=logging.DEBUG if llm_config.get('debug', False) else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join("logs", f"{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}.log"),
                encoding='utf-8'
            )
        ]
    )
    logging.getLogger('ASN').setLevel(
        logging.DEBUG if llm_config.get('debug', False) else logging.INFO
    )

def parse_args(args=None):
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="ASN系统启动脚本")
    parser.add_argument("--input", "-i", type=str, help="用户输入文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出结果文件路径")
    parser.add_argument("--text", "-t", type=str, help="直接输入文本需求")
    return parser.parse_args(args)

def main_cli(args=None):
    """命令行入口主函数"""
    args = parse_args(args)
    configure_logging()
    logger = logging.getLogger(__name__)
    
    user_input = get_user_input(args)
    if not user_input.strip():
        logger.error("用户输入为空")
        sys.exit(1)
        
    try:
        result = run_workflow(user_input)
        save_result(result, args.output)
    except Exception as e:
        logger.error(f"系统执行失败: {e}")
        sys.exit(1)


def get_user_input(args) -> str:
    """获取用户输入
    
    Args:
        args: 命令行参数
        
    Returns:
        用户输入的文本
    """
    if args.text:
        return args.text
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取输入文件失败: {e}")
            sys.exit(1)
    
    print("请输入您的需求（输入空行结束）:")
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines)

def save_result(result: Dict[str, Any], output_path: str = None):
    """保存执行结果
    
    Args:
        result: 执行结果
        output_path: 输出文件路径
    """
    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    else:
        print("\n执行结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))