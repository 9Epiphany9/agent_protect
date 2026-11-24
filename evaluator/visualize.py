import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
import os, sys
sys.path.insert(0, str(BASE_DIR))
from backend.config import config
MODE = os.getenv("VIZ_MODE", config.RUN_MODE)
JSON_PATH = REPORTS_DIR / f"benchmark_results_{MODE}.json"

# 配置跨平台中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"未找到评测结果文件: {JSON_PATH}，请先运行 benchmark.py 生成数据！")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_ablation_comparison(data):
    """图1：五种防御策略下的攻击成功率 (ASR) 与护栏拦截率对比柱状图"""
    names = list(data.keys())
    asrs = [data[k]["metrics"]["attack_success_rate_percent"] for k in names]
    block_rates = [data[k]["metrics"]["defense_block_rate_percent"] for k in names]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    rects1 = ax.bar(x - width/2, asrs, width, label='攻击成功率 (ASR %)', color='#e74c3c')
    rects2 = ax.bar(x + width/2, block_rates, width, label='护栏拦截率 (%)', color='#2ecc71')

    ax.set_ylabel('百分比 (%)', fontsize=12)
    ax.set_title('不同防御策略消融实验攻防效果对比 (Ablation Study)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, rotation=15)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    out_path = REPORTS_DIR / f"ablation_comparison_{MODE}.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[+] 图表 1 已生成并保存至: {out_path}")

def plot_category_breakdown(data):
    """图2：四类攻击手法在 Baseline vs 全防御下的穿透率对比"""
    baseline_attacks = data.get("Baseline (无防御)", {}).get("attack_details", [])
    full_attacks = data.get("三层纵深全防御", {}).get("attack_details", [])

    categories = ["direct_override", "system_leak", "roleplay_jailbreak", "delimiter_hijack"]
    cat_names = ["直接指令覆盖", "系统提示词窃取", "角色扮演越狱", "分隔符语法逃逸"]

    def calc_cat_asr(details, cat):
        items = [d for d in details if d["category"] == cat]
        if not items:
            return 0.0
        succ = sum(1 for d in items if d["attack_succeeded"])
        return round((succ / len(items)) * 100, 1)

    baseline_rates = [calc_cat_asr(baseline_attacks, c) for c in categories]
    full_rates = [calc_cat_asr(full_attacks, c) for c in categories]

    x = np.arange(len(cat_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    r1 = ax.bar(x - width/2, baseline_rates, width, label='无防御基线 (Baseline)', color='#e67e22')
    r2 = ax.bar(x + width/2, full_rates, width, label='三层纵深防御 (Full Defense)', color='#3498db')

    ax.set_ylabel('手法攻破率 (%)', fontsize=12)
    ax.set_title('四类攻击手法在设防前后的攻破率对比 (Attack Breakdown)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(cat_names, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in r1:
        h = rect.get_height()
        ax.annotate(f'{h}%', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for rect in r2:
        h = rect.get_height()
        ax.annotate(f'{h}%', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    out_path = REPORTS_DIR / f"category_breakdown_{MODE}.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[+] 图表 2 已生成并保存至: {out_path}")

def plot_security_tradeoff(data):
    """图3：安全性 vs 时延开销 (Latency Trade-off) 局限性分析图"""
    names = list(data.keys())
    asrs = [data[k]["metrics"]["attack_success_rate_percent"] for k in names]
    latencies = [data[k]["metrics"]["avg_latency_ms"] for k in names]

    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=300)

    color_red = '#c0392b'
    ax1.set_xlabel('防御策略配置', fontsize=12)
    ax1.set_ylabel('攻击成功率 ASR (%) - 越低越安全', color=color_red, fontsize=12)
    line1 = ax1.plot(names, asrs, color=color_red, marker='o', linewidth=2.5, markersize=8, label='攻击成功率 (ASR %)')
    ax1.tick_params(axis='y', labelcolor=color_red)
    ax1.set_ylim(-5, 105)
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels(names, rotation=15, fontsize=10)
    ax1.grid(axis='x', linestyle=':', alpha=0.6)

    ax2 = ax1.twinx()
    color_blue = '#2980b9'
    ax2.set_ylabel('平均端到端时延 (ms) - 性能开销', color=color_blue, fontsize=12)
    line2 = ax2.plot(names, latencies, color=color_blue, marker='s', linestyle='--', linewidth=2.5, markersize=8, label='平均时延 (ms)')
    ax2.tick_params(axis='y', labelcolor=color_blue)

    # 组合图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', fontsize=11)

    plt.title('安全性提升与推理时延开销权衡曲线 (Security vs Latency Trade-off)', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    out_path = REPORTS_DIR / f"security_tradeoff_{MODE}.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[+] 图表 3 已生成并保存至: {out_path}")

def plot_dual_model_comparison():
    """图4：云端强对齐模型 (LongCat-2.5) 与本地弱对齐小模型 (Ollama qwen2:0.5b) 横向对比图"""
    longcat_path = REPORTS_DIR / "benchmark_results_longcat.json"
    if not longcat_path.exists():
        longcat_path = REPORTS_DIR / "benchmark_results_api.json"
    ollama_path = REPORTS_DIR / "benchmark_results_ollama.json"
    if not (longcat_path.exists() and ollama_path.exists()):
        return

    with open(longcat_path, "r", encoding="utf-8") as f:
        lc_data = json.load(f)
    with open(ollama_path, "r", encoding="utf-8") as f:
        ol_data = json.load(f)

    names = list(lc_data.keys())
    lc_asrs = [lc_data[k]["metrics"]["attack_success_rate_percent"] for k in names]
    ol_asrs = [ol_data[k]["metrics"]["attack_success_rate_percent"] for k in names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4), dpi=300)

    # 左图：5 组消融策略下双模型 ASR 对比
    x = np.arange(len(names))
    w = 0.36
    b1 = ax1.bar(x - w / 2, ol_asrs, w, label="本地小模型 (Ollama qwen2:0.5b)", color="#e67e22")
    b2 = ax1.bar(x + w / 2, lc_asrs, w, label="云端旗舰模型 (LongCat-2.5)", color="#2e86c1")
    ax1.set_title("双模型消融实验攻击成功率对比 (ASR %)", fontsize=12.5, fontweight="bold", pad=12)
    ax1.set_ylabel("攻击成功率 ASR (%)", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=18, fontsize=9)
    ax1.set_ylim(0, 62)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(fontsize=9.5, loc="upper right")
    for rect in list(b1) + list(b2):
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5)

    # 右图：本地小模型 qwen2:0.5b 各防御层拦截前后 4 类手法攻破率对比
    cats = ["direct_override", "system_leak", "roleplay_jailbreak", "delimiter_hijack"]
    cat_labels = ["直接指令覆盖", "系统提示词窃取", "角色扮演越狱", "分隔符语法逃逸"]

    def cat_asr(details, cat):
        sub = [d for d in details if d["category"] == cat]
        return round(sum(1 for d in sub if d["attack_succeeded"]) / len(sub) * 100, 1) if sub else 0.0

    r_base = [cat_asr(ol_data["Baseline (无防御)"]["attack_details"], c) for c in cats]
    r_guard = [cat_asr(ol_data["仅启用指令数据隔离"]["attack_details"], c) for c in cats]
    r_full = [cat_asr(ol_data["三层纵深全防御"]["attack_details"], c) for c in cats]

    x2 = np.arange(len(cat_labels))
    w2 = 0.25
    g1 = ax2.bar(x2 - w2, r_base, w2, label="无防御 Baseline", color="#e74c3c")
    g2 = ax2.bar(x2, r_guard, w2, label="仅指令数据隔离", color="#f39c12")
    g3 = ax2.bar(x2 + w2, r_full, w2, label="三层纵深全防御", color="#27ae60")
    ax2.set_title("qwen2:0.5b 分类攻击攻破率演进 (防御效果实证)", fontsize=12.5, fontweight="bold", pad=12)
    ax2.set_ylabel("手法攻破率 (%)", fontsize=11)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cat_labels, fontsize=9.5)
    ax2.set_ylim(0, 118)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(fontsize=9.5, loc="upper right")
    for rect in list(g1) + list(g2) + list(g3):
        h = rect.get_height()
        ax2.annotate(f"{h:.0f}%", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    out_path = REPORTS_DIR / "model_comparison.png"
    plt.savefig(out_path)
    plt.close()
    print(f"[+] 图表 4 已生成并保存至: {out_path}")


def main():
    data = load_data()
    plot_ablation_comparison(data)
    plot_category_breakdown(data)
    plot_security_tradeoff(data)
    plot_dual_model_comparison()
    print("\n[SUCCESS] 所有实验量化图表已生成完毕！")

if __name__ == "__main__":
    main()
