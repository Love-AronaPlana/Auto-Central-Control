import os
import sys
import logging
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
def load_env():
    # 检查.env文件是否存在，如果不存在则从.env.example复制一份
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("已从.env.example创建.env文件，请修改配置后重新运行")
            sys.exit(0)
        else:
            print("错误：未找到.env或.env.example文件")
            sys.exit(1)
    
    # 加载.env文件
    load_dotenv()
    
    # 检查必要的环境变量
    required_vars = ['OPENAI_API_KEY', 'OPENAI_API_BASE', 'OPENAI_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"错误：缺少必要的环境变量: {', '.join(missing_vars)}")
        sys.exit(1)

# 初始化日志
def init_logging(debug=False):
    # 创建log目录（如果不存在）
    if not os.path.exists('log'):
        os.makedirs('log')
    
    # 设置日志级别
    log_level = logging.DEBUG if debug else getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
    
    # 配置日志格式
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"log/acc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    
    # 清理旧日志文件（保留最近10个）
    log_files = sorted([f for f in os.listdir('log') if f.startswith('acc_')], reverse=True)
    for old_file in log_files[10:]:
        try:
            os.remove(os.path.join('log', old_file))
        except Exception as e:
            print(f"无法删除旧日志文件 {old_file}: {e}")

# 初始化内存目录
def init_memory():
    # 清空memory目录
    if os.path.exists('memory'):
        for file in os.listdir('memory'):
            file_path = os.path.join('memory', file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"无法删除内存文件 {file_path}: {e}")
    else:
        os.makedirs('memory')

# 主函数
def main(debug=False):
    # 加载环境变量
    load_env()
    
    # 设置DEBUG环境变量
    os.environ['DEBUG'] = str(debug).lower()
    
    # 初始化日志
    init_logging(debug)
    
    # 初始化内存
    init_memory()
    
    # 导入工作流模块
    from workflow.main_workflow import start_workflow
    
    # 启动工作流
    logging.info("启动Auto-Central-Control系统")
    start_workflow()

# 直接运行此脚本时的入口点
if __name__ == "__main__":
    # 检查是否有命令行参数指定debug模式
    debug_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'debug'
    main(debug_mode)