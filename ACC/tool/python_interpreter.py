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
import sys
from typing import Dict, Any

from ACC.tool.base import BaseTool

logger = logging.getLogger(__name__)

# 修改路径生成方式，使用Path对象增强跨平台兼容性
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"

def add_encoding_handling(code: str) -> str:
    # 统一处理不同平台的路径分隔符
    code = re.sub(
        r'open\(([^,]+),\s*[\'"]r[\'"](,\s*encoding=[\'"][^\'"]+[\'"])?\)',
        r'open(\1, "r", encoding="utf-8"\2)',
        code,
        flags=re.MULTILINE
    )
    # 跨平台路径标准化处理
    code = re.sub(
        r'(with\s+open\(.*?)(\\|/){2,}',
        r'\1os.path.normpath(',
        code,
        flags=re.MULTILINE
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
        temp_filepath = EXAMPLES_DIR / temp_filename  # 使用Path对象替代os.path.join
        
        try:
            # 跨平台目录创建
            EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
            
            # 统一使用Path对象进行文件操作
            with temp_filepath.open("w", encoding="utf-8") as f:
                f.write(processed_code)

            # 设置环境变量
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # 执行Python脚本（删除重复的run调用）
            result = subprocess.run(
                [sys.executable, str(temp_filepath)],
                capture_output=True,
                env=env,
                text=False  # 使用二进制模式，让 chardet 正确检测编码
            )
            
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
            # 清理临时文件（统一使用 Path）
            try:
                if temp_filepath.exists():
                    temp_filepath.unlink()
                    logger.info(f"临时Python脚本已删除: {temp_filepath}")
            except Exception as e:
                logger.error(f"删除临时Python脚本时发生错误: {str(e)}")


# 注册工具
from ACC.tool.base import ToolRegistry
ToolRegistry.register(PythonInterpreterTool())