from typing import Dict, Any
from ASN.agent.base import BaseAgent
from ASN.prompt.ordinary_reply import ORDINARY_REPLY_PROMPT
import logging

logger = logging.getLogger(__name__)


class OrdinaryReplyAgent(BaseAgent):
    """普通回复代理，处理无需规划的简单请求"""

    def __init__(self):
        super().__init__(
            name="Ordinary Reply Agent", system_prompt=ORDINARY_REPLY_PROMPT
        )
        logger.info("初始化普通回复代理")

    def run(self, user_input: str) -> Dict[str, Any]:
        try:
            self.add_message("user", user_input)
            response = self.send_to_llm()
            return self.parse_json_response(response)
        except Exception as e:
            return {"reply": f"普通回复失败: {str(e)}，已收到您的请求"}
