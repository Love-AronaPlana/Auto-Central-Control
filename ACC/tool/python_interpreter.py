"""Python解释器工具

该模块提供了临时执行Python脚本的工具，允许AI执行Python代码。
工具会在examples目录下创建临时文件，执行后返回结果，并自动清理。
"""

import logging
import os
import subprocess
import tempfile
import uuid
import re
import chardet
from typing import Dict, Any

from ACC.tool.base import BaseTool

logger = logging.getLogger(__name__)

# 获取examples目录的绝对路径
EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "examples",
)


def add_encoding_handling(code: str) -> str:
    """添加编码处理代码
    
    在Python代码中添加统一使用utf-8编码的功能
    
    Args:
        code: 原始Python代码
        
    Returns:
        添加了编码处理的Python代码
    """
    # 添加编码检测函数
    encoding_detection_code = """
# 添加编码处理函数
def detect_encoding(file_path):
    \"\"\"检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        检测到的编码，如果检测失败则返回'utf-8'
    \"\"\"
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        if result['confidence'] > 0.7:
            return result['encoding']
        return 'utf-8'  # 默认使用utf-8
    except Exception as e:
        print(f"检测编码时出错: {e}")
        return 'utf-8'
"""
    
    # 检查代码中是否已经定义了detect_encoding函数
    if "def detect_encoding" not in code:
        # 在代码开头添加编码检测函数
        code = encoding_detection_code + "\n" + code
    
    # 替换所有的open调用，添加utf-8编码
    code = re.sub(
        r'open\(([^,]+),\s*[\'"]r[\'"](,\s*encoding=[\'"][^\'"][\'"]\s*)?\)',
        r'open(\1, "r", encoding="utf-8")',
        code
    )
    
    return code


class PythonInterpreterTool(BaseTool):
    """Python解释器工具"""

    def __init__(self):
        """初始化Python解释器工具"""
        super().__init__(
            name="python_interpreter",
            description="临时执行Python脚本并返回输出结果（脚本将在examples目录下创建并在执行后删除）"
        )

    def execute(self, code: str) -> Dict[str, Any]:
        """执行Python脚本

        Args:
            code: Python代码内容

        Returns:
            执行结果字典，包含输出内容或错误信息
        """
        # 添加编码处理
        processed_code = add_encoding_handling(code)
        
        # 生成唯一的临时文件名
        temp_filename = f"temp_script_{uuid.uuid4().hex}.py"
        temp_filepath = os.path.join(EXAMPLES_DIR, temp_filename)

        try:
            # 确保examples目录存在
            os.makedirs(EXAMPLES_DIR, exist_ok=True)

            # 写入Python代码到临时文件
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(processed_code)

            logger.info(f"临时Python脚本已创建: {temp_filepath}")

            # 执行Python脚本部分
            import locale
            import sys
            
            # 获取系统默认编码
            system_encoding = locale.getpreferredencoding()
            logger.debug(f"系统默认编码: {system_encoding}")
            
            # 执行Python脚本，设置适当的编码环境
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                [sys.executable, temp_filepath],
                capture_output=True,
                env=env
            )

            # 准备返回结果
            stdout_bytes = result.stdout
            stderr_bytes = result.stderr
            return_code = result.returncode

            # 检测并解码输出
            def decode_output(byte_data):
                if not byte_data:
                    return ""
                try:
                    # 使用chardet检测编码
                    detected = chardet.detect(byte_data)
                    encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
                    logger.debug(f"检测到编码: {encoding}，置信度: {detected['confidence']}")
                    
                    # 使用检测到的编码解码
                    return byte_data.decode(encoding)
                except Exception as e:
                    logger.error(f"解码输出时出错: {e}")
                    # 尝试使用系统默认编码
                    try:
                        import locale
                        system_encoding = locale.getpreferredencoding()
                        logger.debug(f"尝试使用系统默认编码: {system_encoding}")
                        return byte_data.decode(system_encoding, errors='replace')
                    except Exception:
                        # 最后使用替换模式的UTF-8
                        return byte_data.decode('utf-8', errors='replace')

            # 解码标准输出和错误输出
            output = decode_output(stdout_bytes)
            error = decode_output(stderr_bytes)

            if return_code == 0:
                logger.info("Python脚本执行成功")
                return {
                    "status": "success",
                    "output": output,
                    "return_code": return_code
                }
            else:
                logger.error(f"Python脚本执行失败: {error}")
                return {
                    "status": "error",
                    "error": error,
                    "output": output,
                    "return_code": return_code
                }

        except Exception as e:
            logger.exception(f"执行Python脚本时发生错误: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                    logger.info(f"临时Python脚本已删除: {temp_filepath}")
            except Exception as e:
                logger.error(f"删除临时Python脚本时发生错误: {str(e)}")


# 注册工具
from ACC.tool.base import ToolRegistry
ToolRegistry.register(PythonInterpreterTool())