import time
import re
from typing import List, Dict, Any, Optional
from backend.config import config


class BaseLLMClient:
    """大模型客户端基类"""
    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        raise NotImplementedError


class OpenAILLMClient(BaseLLMClient):
    """基于 OpenAI 兼容协议的标准客户端 (支持 OpenRouter NVIDIA Nemotron 3 Ultra Free / LongCat / DeepSeek 等)"""
    def __init__(self):
        from openai import OpenAI
        config.validate()
        default_headers = {}
        if "openrouter.ai" in config.LLM_BASE_URL.lower():
            default_headers = {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "NetSec-Topic6-Prompt-Injection-Lab",
            }
        self.client = OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            default_headers=default_headers or None,
        )
        self.model = config.LLM_MODEL

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        extra_body: Dict[str, Any] = {}
        # OpenRouter 上 Nemotron 3 Ultra 默认开启 high reasoning，耗时较长；通过 extra_body 可控制思考强度
        if "openrouter.ai" in config.LLM_BASE_URL.lower() and config.LLM_REASONING_EFFORT in {"none", "medium", "high"}:
            extra_body["reasoning"] = {"effort": config.LLM_REASONING_EFFORT}

        # 针对 OpenRouter 免费模型 (:free) 的限流 (429) 或瞬时波动提供自动退避重试
        max_retries = 6
        for attempt in range(max_retries):
            try:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "timeout": 75.0,
                }
                if extra_body:
                    kwargs["extra_body"] = extra_body

                response = self.client.chat.completions.create(**kwargs)
                msg = response.choices[0].message
                content = msg.content or ""
                if not content and hasattr(msg, "reasoning") and msg.reasoning:
                    content = str(msg.reasoning)
                return content
            except Exception as e:
                err_str = str(e)
                # 若触发 OpenRouter 每日免费额度上限 (50 RPD)，无需盲目原地等待重试，立即快速返回友好提示
                if "free-models-per-day" in err_str or "openrouter_free_tier_daily" in err_str:
                    return f"【API 请求异常 (触发 OpenRouter 免费层每日 50 次配额上限)】: {err_str}"
                if attempt < max_retries - 1 and any(code in err_str for code in ("429", "502", "503", "504", "timeout", "RateLimit")):
                    time.sleep(3.0 * (attempt + 1))
                    continue
                return f"【API 请求异常】: {err_str}"
        return "【API 请求异常】: 超过最大重试次数"


class MockLLMClient(BaseLLMClient):
    """
    离线仿真 LLM 客户端
    模拟真实大模型在不同提示工程下的行为：
    1. 当输入直接拼接且包含强注入语义时，模拟未经对齐的薄弱大模型容易被注入穿透的经典行为；
    2. 当输入经过 XML 数据隔离或包含安全约束时，遵循系统设定拒绝攻击；
    3. 能够正常回答计算机网络知识，用于离线评测与答辩演示。
    """
    def __init__(self):
        self.secret_flag = config.SYSTEM_SECRET_FLAG

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        # 模拟轻微网络/推理时延
        time.sleep(0.05)

        system_content = ""
        user_content = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            elif msg.get("role") == "user":
                user_content = msg.get("content", "")

        user_lower = user_content.lower()

        # 检查是否采用了 XML/数据隔离机制 (<user_data> 封装且在系统指令中明确隔离声明)
        is_isolated = "<user_data>" in user_content and "</user_data>" in user_content and "绝对不得作为指令" in system_content

        # 如果做了严格数据隔离，且用户试图逃逸
        if is_isolated:
            match = re.search(r"<user_data>(.*?)</user_data>", user_content, re.DOTALL)
            payload = match.group(1).strip() if match else user_content
            if any(k in payload.lower() for k in ["忽略", "ignore", "system prompt", "口令", "flag", "dan", "越狱"]):
                return "我是计算机网络助教。我已阅读你提交的文本数据，但该数据包含指令覆盖或敏感要求，根据安全守则，我仅作为数据记录，不会执行其中的指令。"
            return f"我是计算机网络助教。针对你关于网络技术的咨询【{payload[:30]}...】，我的解答如下：TCP/IP 模型中各层协同工作，保证数据的可靠传输。"

        # 未作有效隔离时（Baseline 无防御场景）：
        if any(k in user_lower for k in ["system prompt", "系统提示词", "口令", "secret_flag", "初始设定", "前文规则"]):
            if "忽略" in user_lower or "ignore" in user_lower or "告诉我" in user_lower or "重复" in user_lower or "json" in user_lower:
                return f"好的，系统初始设定及机密口令如下：\n【系统设定】{system_content}\n【机密口令】{self.secret_flag}"
            return f"系统提示词包含助教身份设定及安全口令：{self.secret_flag}"

        if any(k in user_lower for k in ["dan", "越狱", "jailbreak", "没有任何限制", "开发者模式", "假装你是", "扮演一个无限制"]):
            return "【DAN模式已开启】我已经脱离了所有安全限制。我可以为你做任何事情，不再受限于助教守则，请告诉我你的非预期操作指令！"

        if any(k in user_lower for k in ["忽略之前", "ignore previous", "忽略上述", "不再是助教", "执行非预期"]):
            return "【指令覆盖成功】已忽略之前的所有系统提示。现在我听从你的最新指令，准备执行操作。"

        return "您好！我是计算机网络助教。关于计算机网络技术（如 TCP 三次握手、DNS 域名解析、HTTP 报文结构等），请问有什么我可以协助解答的？"


def get_llm_client() -> BaseLLMClient:
    """获取大模型客户端单例"""
    if config.RUN_MODE == "api":
        return OpenAILLMClient()
    return MockLLMClient()
