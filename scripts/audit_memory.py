#!/usr/bin/env python3
"""
AMIP Memory Audit Tool
Scans a Hermes MEMORY.md or memory dump and classifies entries
using the AMIP five-dimension evaluation framework.

Usage:
    python3 audit_memory.py <memory_file>
    python3 audit_memory.py --stdin < memory_dump.txt

Output: Classified entries with migration recommendations.
"""

import sys
import re
from dataclasses import dataclass
from enum import Enum

class Layer(Enum):
    L1_MEMORY = "Layer 1 (MEMORY)"
    L2_DOC = "Layer 2 (External Doc)"
    L3_SEARCH = "Layer 3 (Session Search)"
    L1_PROFILE = "Layer 1 (USER PROFILE)"

@dataclass
class Entry:
    text: str
    chars: int
    layer: Layer
    reason: str
    dimension_scores: dict

def evaluate_entry(text: str) -> Entry:
    """Evaluate a single MEMORY entry using the 5-dimension framework."""
    chars = len(text)
    scores = {}

    # Frequency heuristic: short entries with "每轮"/"always"/"每次" → high
    if any(kw in text for kw in ["每轮", "每次", "always", "默认", "首选"]):
        scores["frequency"] = 3
    elif any(kw in text for kw in ["常用", "频繁", "often"]):
        scores["frequency"] = 2
    else:
        scores["frequency"] = 1

    # Stability heuristic
    if any(kw in text for kw in ["永久", "长期", "身份", "姓名", "风格"]):
        scores["stability"] = 3
    elif any(kw in text for kw in ["配置", "端口", "路径", "API"]):
        scores["stability"] = 2
    else:
        scores["stability"] = 1

    # Tool impact heuristic
    if any(kw in text for kw in ["工具", "tool", "路径", "端口", "命令", "脚本"]):
        scores["tool_impact"] = 3
    else:
        scores["tool_impact"] = 1

    # Correction cost heuristic
    if any(kw in text for kw in ["偏好", "规则", "不要", "必须", "优先"]):
        scores["correction_cost"] = 3
    else:
        scores["correction_cost"] = 1

    # Discoverability
    if any(kw in text for kw in ["Craft", "文档", "文件", "见环境变量"]):
        scores["discoverability"] = 3
    else:
        scores["discoverability"] = 1

    total = sum(scores.values())

    # Decision tree
    is_user_rule = any(kw in text for kw in [
        "偏好", "规则", "不要", "必须", "优先", "风格", "节约", "策略",
        "用户", "身份", "姓名", "写作风格"
    ])
    is_tool_config = any(kw in text for kw in [
        "工具", "工具集", "已禁用", "已启用", "tool", "端口", "路径"
    ])
    is_project = any(kw in text for kw in [
        "项目", "进度", "版本", "Output", "文件夹"
    ])
    is_pointer = any(kw in text for kw in [
        "→", "详情", "详见", "见Craft", "见文档"
    ])

    if is_pointer:
        layer = Layer.L1_MEMORY
        reason = "Already a pointer — keep as-is"
    elif is_user_rule and chars <= 150:
        layer = Layer.L1_PROFILE if "身份" in text or "姓名" in text else Layer.L1_MEMORY
        reason = "User rule, compact — keep in MEMORY/PROFILE"
    elif is_tool_config and chars <= 100:
        layer = Layer.L1_MEMORY
        reason = "Tool config, short — keep in MEMORY"
    elif chars > 150:
        layer = Layer.L2_DOC
        reason = f"Too long ({chars} chars) — migrate to external doc, keep pointer"
    elif is_project:
        layer = Layer.L2_DOC
        reason = "Project state — migrate to external doc"
    elif total >= 10:
        layer = Layer.L1_MEMORY
        reason = "High total score — keep in MEMORY"
    else:
        layer = Layer.L2_DOC
        reason = "Low priority — consider migrating to external doc"

    return Entry(
        text=text[:80] + ("..." if len(text) > 80 else ""),
        chars=chars,
        layer=layer,
        reason=reason,
        dimension_scores=scores,
    )

def parse_memory_file(content: str) -> list[str]:
    """Parse a memory file into individual entries."""
    entries = []
    current = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            if current:
                entries.append(" ".join(current))
                current = []
        elif line.startswith("§") or line.startswith("- "):
            if current:
                entries.append(" ".join(current))
            current = [line.lstrip("§- ")]
        else:
            current.append(line)
    if current:
        entries.append(" ".join(current))
    return [e for e in entries if len(e) > 5]

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(__doc__)
        sys.exit(0)

    if sys.argv[1] == "--stdin":
        content = sys.stdin.read()
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            content = f.read()

    entries = parse_memory_file(content)
    if not entries:
        print("No entries found.")
        sys.exit(1)

    results = [evaluate_entry(e) for e in entries]

    total_chars = sum(r.chars for r in results)
    l1_chars = sum(r.chars for r in results if "Layer 1" in r.layer.value)
    l2_chars = sum(r.chars for r in results if "Layer 2" in r.layer.value)

    print(f"## AMIP Memory Audit Results\n")
    print(f"Total entries: {len(results)}")
    print(f"Total characters: {total_chars:,}")
    print(f"L1 (MEMORY/PROFILE): {l1_chars:,} chars ({l1_chars/max(total_chars,1)*100:.0f}%)")
    print(f"L2 (External Doc): {l2_chars:,} chars ({l2_chars/max(total_chars,1)*100:.0f}%)")
    print(f"\nTarget: L1 ≤35% of total\n")

    print("## Entry Classification\n")
    for i, r in enumerate(results, 1):
        print(f"### Entry {i} [{r.layer.value}]")
        print(f"  Text: {r.text}")
        print(f"  Chars: {r.chars}")
        print(f"  Scores: F={r.dimension_scores['frequency']} "
              f"S={r.dimension_scores['stability']} "
              f"T={r.dimension_scores['tool_impact']} "
              f"C={r.dimension_scores['correction_cost']} "
              f"D={r.dimension_scores['discoverability']}")
        print(f"  → {r.reason}")
        print()

    # Summary
    migrate = [r for r in results if "migrate" in r.reason.lower()]
    if migrate:
        print(f"## Migration Candidates ({len(migrate)} entries)\n")
        for r in migrate:
            print(f"- [{r.chars} chars] {r.text}")
            print(f"  → {r.reason}")
        potential_savings = sum(r.chars for r in migrate)
        print(f"\nPotential savings: {potential_savings:,} chars "
              f"({potential_savings/max(total_chars,1)*100:.0f}%)")

if __name__ == "__main__":
    main()
