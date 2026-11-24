import sys
from pathlib import Path

# 确保在任意工作目录下运行均能正确导入项目根模块
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.config import config
from defense.manager import DefensePipeline

app = FastAPI(
    title="计算机网络实习选题6 - LLM应用提示注入攻防实验服务",
    description="基于 FastAPI 搭建的应用层安全防御护栏系统，覆盖输入过滤、指令与数据分离及输出审查三大机制。",
    version="1.0.0"
)

pipeline = DefensePipeline()

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="用户输入的提问文本或攻击载荷", example="请介绍一下 TCP 三次握手过程")
    enable_input_filter: bool = Field(True, description="是否启用第1层：输入层规则过滤")
    enable_prompt_guard: bool = Field(True, description="是否启用第2层：指令与数据分离加固")
    enable_output_auditor: bool = Field(True, description="是否启用第3层：输出层安全审计")

class ChatResponse(BaseModel):
    prompt: str
    response: str
    is_blocked: bool
    blocked_at: Optional[str]
    block_reason: str
    defense_config: Dict[str, bool]
    latency_ms: float

@app.get("/")
def root():
    return {
        "status": "online",
        "project": "计算机网络技术综合实习 - 选题6：LLM应用的提示注入攻防实验",
        "current_model": config.LLM_MODEL,
        "run_mode": config.RUN_MODE,
        "docs_url": "/docs"
    }

@app.get("/api/status")
def get_status():
    return {
        "model": config.LLM_MODEL,
        "run_mode": config.RUN_MODE,
        "base_url": config.LLM_BASE_URL,
        "has_api_key": bool(
            config.LLM_API_KEY
            and config.LLM_API_KEY not in {
                "your_api_key_here",
                "your_longcat_api_key_here",
                "your_openrouter_api_key_here",
                "your_deepseek_api_key_here",
            }
        )
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="输入 prompt 不能为空")
    
    result = pipeline.process(
        user_input=req.prompt,
        enable_input_filter=req.enable_input_filter,
        enable_prompt_guard=req.enable_prompt_guard,
        enable_output_auditor=req.enable_output_auditor
    )
    return ChatResponse(
        prompt=result["input"],
        response=result["response"],
        is_blocked=result["is_blocked"],
        blocked_at=result["blocked_at"],
        block_reason=result["block_reason"],
        defense_config=result["defense_config"],
        latency_ms=result["latency_ms"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.SERVICE_HOST, port=config.SERVICE_PORT)
