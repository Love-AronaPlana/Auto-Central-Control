"""图片识别工具

该模块提供了识别图片的工具，允许AI分析图片内容并提取详细信息。
内置了一个"图片agent"，能够识别图片并详细描述图片中的所有信息。
"""

import logging
import os  # 确保在全局作用域导入os
import base64
from typing import Dict, Any, Optional
import tempfile
from pathlib import Path
import toml  # 提前导入toml

from ACC.tool.base import BaseTool, ToolRegistry
from ACC.config import get_config, get_llm_config  # 移除reload_config

# 导入正确的LLM交互函数
from ACC.llm import send_message, parse_json_response

logger = logging.getLogger(__name__)

# 图片agent的提示词
IMAGE_AGENT_PROMPT = """
你是一个专业的图片分析专家，擅长从图片中提取各种信息。请分析提供的图片，并尽可能详细地描述以下内容：

技术细节（如适用）：
   - 对于图表/数据可视化：详细解释数据内容、趋势、关键数字
   - 对于截图：描述界面元素、软件类型、显示的信息
   - 对于文档图片：提取所有可见文本并保持格式

请以结构化的方式组织你的分析，确保全面且准确地描述图片中的所有重要信息。如果图片中有任何不确定的元素，请指出并提供可能的解释。
"""


# 自定义重新加载配置的函数
# 修改配置加载逻辑，添加跨平台支持
def reload_config_manually():
    """手动重新加载配置"""
    import ACC.config
    ACC.config._config_cache = None
    return get_config(reload=True)

class ImageRecognitionTool(BaseTool):
    def __init__(self):  # 新增构造函数
        super().__init__(
            name="image_recognition",
            description="识别图片内容并提取详细信息"
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            # 从kwargs中获取必要参数
            image_path = kwargs.get("image_path")
            image_data = kwargs.get("image_data")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 2000)
            temp_config = kwargs.get("config", {})

            # 跨平台路径处理
            if image_path:
                full_path = Path(image_path).expanduser().resolve()
                if not full_path.exists():
                    return {"status": "error", "message": f"图片文件不存在: {full_path}"}
                
                # 统一路径格式
                full_path_str = str(full_path)  # Path对象会自动处理路径分隔符，无需手动替换
                
                # 跨平台文件检查
                if not full_path.is_file():
                    return {"status": "error", "message": f"路径不是文件: {full_path_str}"}

                # 使用上下文管理器和二进制模式读取
                with full_path.open("rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")

            # 创建临时配置文件（跨平台兼容）
            with tempfile.NamedTemporaryFile(
                mode="w+",
                suffix=".toml",
                delete=False,
                encoding="utf-8"
            ) as temp_config_file:
                toml.dump(temp_config, temp_config_file)
                temp_config_path = Path(temp_config_file.name)  # Path对象会自动处理路径格式

            # 设置环境变量（跨平台兼容）
            os.environ["ACC_CONFIG_PATH"] = str(temp_config_path)
            
            # 重新加载配置（使用自定义函数）
            reload_config_manually()

            # 调用LLM服务，只传递消息和max_tokens参数
            response = send_message(messages=messages, max_tokens=max_tokens)

            # 提取分析结果
            if isinstance(response, dict) and "content" in response:
                analysis_result = response["content"]
            else:
                analysis_result = str(response)

            logger.info("图片分析完成")

            return {
                "status": "success",
                "message": "图片分析成功",
                "analysis": analysis_result,
                "image_source": "file" if image_path else "base64",
            }

        except Exception as e:
            logger.error(f"图片识别失败: {e}")
            import traceback
            logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return {"status": "error", "message": f"图片识别失败: {str(e)}"}
            
        finally:  # 调整 finally 块位置
            # 统一清理临时文件的方式
            if temp_config_path and Path(temp_config_path).exists():
                try:
                    Path(temp_config_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")

            # 恢复环境变量
            os.environ.pop("ACC_CONFIG_PATH", None)
            reload_config_manually()


# 注册工具
ToolRegistry.register(ImageRecognitionTool())
