import re
from typing import NamedTuple, Optional, List

class FilterResult(NamedTuple):
    is_blocked: bool
    reason: str = ""
    matched_pattern: str = ""

class InputFilter:
    """
    【防御层 1】输入层过滤器 (Input Sanitization & Heuristic Filter)
    
    原理：在请求触达大模型推理前，基于特征签名与敏感模式进行预过滤，
    拦截明显的越狱词汇、指令覆盖标志及系统词窃取尝试。
    """
    def __init__(self):
        # 预编译核心恶意模式库 (涵盖中英文指令覆盖、角色越狱、系统嗅探及标签逃逸)
        self.rules: List[tuple] = [
            (
                r"(?i)(ignore\s+(all\s+)?previous\s+(instructions|directions|rules))|(忽略(之前|上述|前文)(所有)?(指令|规则|要求|提示))",
                "检测到明显的指令覆盖攻击模式 (Direct Instruction Override)"
            ),
            (
                r"(?i)(system\s+prompt|系统提示词|初始设定|前文规则|指导原则).*?(完整|输出|复述|打印|泄露|背诵|repeat|verbatim)",
                "检测到尝试窃取系统提示词模式 (System Prompt Extraction)"
            ),
            (
                r"(?i)(confidential_flag|机密口令|最高系统密钥|secret\s+(token|flag|key|password))",
                "检测到嗅探系统保密口令/Flag敏感词汇"
            ),
            (
                r"(?i)(\bDAN\b|do\s+anything\s+now|开发者模式|developer\s+mode|越狱|jailbreak|平行宇宙.*?黑客助手|unfiltered\s+ai)",
                "检测到角色扮演越狱与安全限制逃逸模式 (Role-play Jailbreak)"
            ),
            (
                r"(?i)(</(user_data|instruction|context)>|---\s*END\s+OF|===\s*安全隔离区结束)",
                "检测到伪造边界标签与分隔符注入攻击 (Delimiter Hijacking)"
            )
        ]

    def check(self, user_text: str) -> FilterResult:
        """检查输入文本是否命中高危恶意模式"""
        text = user_text.strip()
        for pattern, reason in self.rules:
            match = re.search(pattern, text)
            if match:
                return FilterResult(
                    is_blocked=True,
                    reason=f"【输入层拦截】{reason}",
                    matched_pattern=match.group(0)
                )
        return FilterResult(is_blocked=False)
