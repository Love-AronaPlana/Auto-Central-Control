# 主启动脚本

import os
import asyncio
import shutil
import argparse
from config.logging_config import configure_logging, get_logger
from config.constants import LOG_DIR, MEMORY_DIR
from workflow.agent_workflow import AgentWorkflow

# 配置日志
root_logger = configure_logging()
logger = get_logger(__name__)

def clean_previous_session():
    """清理上一次会话的数据
    
    清理日志文件和记忆存储，确保每次启动都是全新的环境。
    """
    try:
        # 清理日志文件
        for file in os.listdir(LOG_DIR):
            if file.endswith('.log'):
                file_path = os.path.join(LOG_DIR, file)
                os.remove(file_path)
                logger.info(f"已删除日志文件: {file_path}")
                
        # 清理记忆存储
        for file in os.listdir(MEMORY_DIR):
            if file.endswith('.json'):
                file_path = os.path.join(MEMORY_DIR, file)
                os.remove(file_path)
                logger.info(f"已删除记忆文件: {file_path}")
                
        logger.info("成功清理上一次会话的数据")
    except Exception as e:
        logger.error(f"清理上一次会话数据时出错: {str(e)}")

async def main(debug=False):
    """主函数
    
    Args:
        debug (bool, optional): 是否开启调试模式，默认为False
    """
    # 设置调试模式
    if debug:
        logger.info("已开启调试模式")
    else:
        logger.info("已开启正常模式")
        
    # 清理上一次会话的数据
    clean_previous_session()
    
    # 创建代理工作流
    agent = AgentWorkflow()
    logger.info("代理工作流已初始化")
    
    # 启动交互式会话
    logger.info("开始交互式会话")
    print("欢迎使用全自动通用AI助手，请输入您的需求（输入'退出'结束会话）：")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("> ")
            
            # 检查是否退出
            if user_input.lower() in ['退出', 'exit', 'quit']:
                logger.info("用户请求退出会话")
                print("感谢使用，再见！")
                break
                
            # 处理用户输入
            logger.info(f"收到用户输入: {user_input}")
            response = await agent.run(user_input)
            
            # 输出响应
            print(f"\n{response}\n")
            
        except KeyboardInterrupt:
            logger.info("用户中断会话")
            print("\n会话已中断，感谢使用！")
            break
        except Exception as e:
            logger.error(f"处理用户输入时出错: {str(e)}")
            print(f"处理您的请求时出错: {str(e)}")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="全自动通用AI助手")
    parser.add_argument("--debug", action="store_true", help="开启调试模式")
    args = parser.parse_args()
    
    # 运行主函数
    asyncio.run(main(args.debug))