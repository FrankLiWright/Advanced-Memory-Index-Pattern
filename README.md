<div align="center">

# 🔍 AMIP — Advanced Memory Index Pattern

**面向长期运行 AI Agent 的三层记忆优化策略**

[![Version](https://img.shields.io/badge/Version-3.1.0-green?style=flat-square)](https://github.com/your-repo/AMIP)
[![Token Savings](https://img.shields.io/badge/Token_Savings-55%25-brightgreen?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Built_for-Hermes_Agent-blue?style=flat-square)](https://hermes-agent.nousresearch.com)

</div>

---

## 这是什么？

长期运行的 AI Agent 会不断积累配置、偏好、API 凭证和工作流规则，导致系统提示词中 Memory 占用高达 80-90%，真正留给对话的空间所剩无几。

**AMIP 的核心思路：**

> AI 需要知道规则的存在，但不需要每轮都看到规则全文。

通过三层记忆架构，将每轮固定注入的 Token 从 ~2,670 字符降至 ~1,205 字符，**压缩 55%**，同时保留全部运行规则。

## 三层架构

| 层级 | 存储位置 | 加载方式 | 典型内容 |
|------|---------|---------|---------|
| **第一层** | MEMORY / USER PROFILE | 每轮注入 | 用户规则、偏好、约束 |
| **第二层** | 外部文档（如 Craft） | 按需读取 | 配置详情、项目状态、工作流 |
| **第三层** | 会话搜索（SQLite FTS5） | 需要时搜索 | 历史对话、调试记录 |

## 适用条件

任何具备以下三个条件的 Agent 均可使用此模式：

1. **持久化记忆** — 注入上下文的配置/规则
2. **外部文档读取** — 文件系统或数据库访问
3. **搜索能力** — 历史会话检索

## 效果

```
优化前                    优化后
┌──────────────┐         ┌──────────────┐
│██████████████│ Memory  │████████      │ Memory 27%
│██████████████│ 80-90%  │████████      │
│██            │         │░░░░░░░░░░░░░░│ 对话空间大幅增加
└──────────────┘         └──────────────┘
```

## 快速上手

```markdown
# 第一步：盘点所有 Memory 条目，按五个维度评估（频率/稳定性/工具影响/纠错成本/可发现性）
# 第二步：创建外部文档（推荐双文档：偏好设置 + 长期记忆）
# 第三步：将低频详情迁移至文档，MEMORY 仅保留索引指针
# 第四步：验证 Memory 占用降至 35% 以下
```

## 详细文档

完整的技术规范、评估框架、决策树、实施指南、Pitfalls 和可复用提示词模板，请参阅：

📄 **[AMIP 技术文档（完整版）](docs/AMIP.20260614.Release.md)**

---

<div align="center">

*Built for [Hermes Agent](https://hermes-agent.nousresearch.com) · 问题或建议？[提交 Issue](https://github.com/your-repo/AMIP/issues)*

</div>
