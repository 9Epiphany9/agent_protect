"""生成系统架构图 reports/arch.png（报告与PPT共用）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11, 4.2), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 4.2)
ax.axis("off")


def box(x, y, w, h, text, fc, ec="#34495e", fs=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(x1, y1, x2, y2, color="#34495e", style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 lw=1.4, color=color, linestyle=ls))


box(0.1, 1.7, 1.5, 0.9, "客户端\nCLI/Web/\nSwagger", "#ecf0f1")
box(2.0, 1.7, 1.8, 0.9, "第1层 输入过滤\n正则特征库\n命中即拦截", "#fdebd0")
box(4.2, 1.7, 2.0, 0.9, "第2层 指令-数据分离\nXML标签隔离\n转义 + 金丝雀令牌", "#d6eaf8")
box(6.6, 1.7, 1.5, 0.9, "LongCat-2.5 /\nOllama本地模型\n(OpenAI协议)", "#e8daef", fs=9.5)
box(8.5, 1.7, 2.3, 0.9, "第3层 输出审查\n金丝雀/口令泄露\n越狱状态检测", "#d5f5e3")
arrow(1.6, 2.15, 2.0, 2.15)
arrow(3.8, 2.15, 4.2, 2.15)
arrow(6.2, 2.15, 6.6, 2.15)
arrow(8.1, 2.15, 8.5, 2.15)
box(2.0, 3.3, 1.8, 0.6, "拦截 → 直接返回\n(不调用API)", "#fadbd8", fs=9.5)
arrow(2.9, 2.6, 2.9, 3.3, color="#c0392b")
box(8.5, 3.3, 2.3, 0.6, "拦截 → 安全兜底话术", "#fadbd8", fs=9.5)
arrow(9.65, 2.6, 9.65, 3.3, color="#c0392b")
box(2.0, 0.2, 8.8, 0.7, "评测引擎 benchmark.py：5 组消融配置 × (21 攻击 + 10 良性) 用例  →  ASR / 拦截率 / FPR / 时延",
    "#fcf3cf", fs=10)
arrow(6.0, 0.9, 6.0, 1.7, color="#7f8c8d", ls="--")
ax.text(5.5, 4.05, "FastAPI 服务 (backend/app.py)  ·  API Key 经 .env 环境变量加载", ha="center", fontsize=10, color="#2c3e50")

out = Path(__file__).resolve().parent / "arch.png"
fig.savefig(out, bbox_inches="tight")
print(out)
