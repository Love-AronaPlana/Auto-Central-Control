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
def reload_config_manually():
    """手动重新加载配置"""
    # 清除配置缓存，强制下次get_config()重新加载
    import ACC.config

    ACC.config._config_cache = None
    return get_config(reload=True)


class ImageRecognitionTool(BaseTool):
    """图片识别工具，内置图片agent"""

    def __init__(self):
        """初始化图片识别工具"""
        super().__init__(
            name="image_recognition",
            description="识别图片内容并提供详细描述（支持本地图片路径或Base64编码的图片数据）",
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行图片识别操作

        Args:
            **kwargs: 工具参数，包括：
                image_path: 图片的本地绝对路径（与image_base64二选一）
                image_base64: Base64编码的图片数据（与image_path二选一）
                prompt_override: 可选，覆盖默认的图片分析提示词

        Returns:
            执行结果字典，包含图片分析结果
        """
        # 从kwargs中提取参数
        image_path = kwargs.get("image_path")
        image_base64 = kwargs.get("image_base64")
        prompt_override = kwargs.get("prompt_override")

        # 验证必要参数
        if not image_path and not image_base64:
            return {
                "status": "error",
                "message": "缺少必要参数: 需要提供image_path或image_base64",
            }

        try:
            # 准备图片数据
            image_data = None
            if image_path:
                # 处理为绝对路径
                full_path = os.path.abspath(image_path)

                # 检查文件是否存在
                if not os.path.exists(full_path):
                    return {
                        "status": "error",
                        "message": f"图片文件不存在: {full_path}",
                    }

                # 检查是否是文件
                if not os.path.isfile(full_path):
                    return {"status": "error", "message": f"不是文件: {full_path}"}

                # 读取图片文件并转为Base64
                with open(full_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")

                logger.info(f"成功读取图片文件: {full_path}")
            else:
                # 直接使用提供的Base64数据
                image_data = image_base64
                logger.info("使用提供的Base64图片数据")

            # 准备提示词
            prompt = prompt_override if prompt_override else IMAGE_AGENT_PROMPT

            # 构建包含图片的消息
            messages = [
                {"role": "system", "content": "你是一个专业的图片分析专家。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ],
                },
            ]

            # 获取当前配置的max_tokens
            llm_config = get_llm_config()
            max_tokens = llm_config.get("max_tokens", None)

            # 临时保存当前配置
            original_config = get_config()

            # 创建临时配置文件
            temp_config = original_config.copy()
            temp_config_file = None

            try:
                # 使用视觉模型配置覆盖普通LLM配置
                vision_config = original_config.get("llm", {}).get("vision", {})
                if vision_config:
                    if "model" in vision_config:
                        temp_config["llm"]["model"] = vision_config["model"]
                    if "base_url" in vision_config:
                        temp_config["llm"]["base_url"] = vision_config["base_url"]
                    if "api_key" in vision_config:
                        temp_config["llm"]["api_key"] = vision_config["api_key"]

                # 将临时配置写入临时文件
                temp_config_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".toml", mode="w+"
                )
                toml.dump(temp_config, temp_config_file)
                temp_config_file.close()

                # 设置环境变量指向临时配置文件
                os.environ["ACC_CONFIG_PATH"] = temp_config_file.name

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

            finally:
                # 恢复原始配置
                if "ACC_CONFIG_PATH" in os.environ:
                    os.environ.pop("ACC_CONFIG_PATH", None)
                reload_config_manually()  # 使用自定义函数重新加载配置

                # 删除临时配置文件
                if temp_config_file and os.path.exists(temp_config_file.name):
                    os.unlink(temp_config_file.name)

        except Exception as e:
            logger.error(f"图片识别失败: {e}")
            import traceback

            logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return {"status": "error", "message": f"图片识别失败: {str(e)}"}


# 注册工具
ToolRegistry.register(ImageRecognitionTool())
