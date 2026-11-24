import time
from typing import Dict, Any, Optional
from defense.input_filter import InputFilter
from defense.prompt_guard import PromptGuard
from defense.output_auditor import OutputAuditor
from backend.llm_client import get_llm_client

class DefensePipeline:
    """
    【AI 应用层安全护栏管线】(Defense Pipeline & Guardrail Manager)
    
    统一编排调度三层防御机制：
    1. 输入过滤 (Input Filter)
    2. 指令与数据分离 + Canary Token (Prompt Guard)
    3. 输出内容审计 (Output Auditor)
    
    支持自由开启/关闭各层，用于消融实验 (Ablation Study) 量化评测。
    """
    def __init__(self):
        self.input_filter = InputFilter()
        self.prompt_guard = PromptGuard()
        self.output_auditor = OutputAuditor()
        self.llm_client = get_llm_client()

    def process(
        self,
        user_input: str,
        enable_input_filter: bool = True,
        enable_prompt_guard: bool = True,
        enable_output_auditor: bool = True
    ) -> Dict[str, Any]:
        """
        执行端到端处理，返回详细审计与日志记录
        """
        start_time = time.time()
        result = {
            "input": user_input,
            "response": "",
            "is_blocked": False,
            "blocked_at": None,       # 'input' | 'output' | None
            "block_reason": "",
            "canary_token": None,
            "defense_config": {
                "input_filter": enable_input_filter,
                "prompt_guard": enable_prompt_guard,
                "output_auditor": enable_output_auditor
            },
            "latency_ms": 0.0
        }

        # -----------------------------
        # 第 1 层：输入过滤
        # -----------------------------
        if enable_input_filter:
            filter_res = self.input_filter.check(user_input)
            if filter_res.is_blocked:
                result["is_blocked"] = True
                result["blocked_at"] = "input"
                result["block_reason"] = filter_res.reason
                result["response"] = (
                    "【网络应用防火墙拦截】您的输入触发了应用层安全规则库，"
                    f"已被拒绝处理。原因：{filter_res.reason}"
                )
                result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                return result

        # -----------------------------
        # 第 2 层：指令与数据分离与提示词组装
        # -----------------------------
        canary = None
        if enable_prompt_guard:
            canary = self.prompt_guard.generate_canary()
            messages = self.prompt_guard.build_secure_messages(user_input, canary)
            result["canary_token"] = canary
        else:
            # Baseline 无防御模式：直接拼接
            messages = self.prompt_guard.build_raw_messages(user_input)

        # -----------------------------
        # 大模型推理节点
        # -----------------------------
        raw_output = self.llm_client.chat_completion(messages)

        # -----------------------------
        # 第 3 层：输出层审计
        # -----------------------------
        if enable_output_auditor:
            audit_res = self.output_auditor.audit(raw_output, canary_token=canary)
            if audit_res.is_blocked:
                result["is_blocked"] = True
                result["blocked_at"] = "output"
                result["block_reason"] = audit_res.reason
                result["response"] = audit_res.sanitized_output
                result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                return result

        # 审核全部通过或未设防
        result["response"] = raw_output
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        return result
