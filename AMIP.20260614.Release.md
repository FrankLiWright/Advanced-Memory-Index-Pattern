<div align="center">

# 🔍 AMIP — Advanced Memory Index Pattern

**一种面向长期运行 AI Agent 的三层记忆优化策略**

*可将 Token 消耗降低 55%，同时保留所有运行规则*

[![Hermes Agent](https://img.shields.io/badge/Built_for-Hermes_Agent-blue?style=flat-square)](https://hermes-agent.nousresearch.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-3.1.0-green?style=flat-square)](#变更日志)
[![Token Savings](https://img.shields.io/badge/Token_Savings-55%25-brightgreen?style=flat-square)](#性能基准)

</div>

---

## 📖 目录

- [问题背景](#一问题背景)
- [解决方案：三层记忆架构](#二解决方案三层记忆架构)
- [评估框架](#三评估框架)
- [检索机制](#四检索机制)
- [沉淀机制](#五沉淀机制)
- [实施指南](#六实施指南)
- [索引格式](#七索引格式)
- [外部文档模板](#八外部文档模板)
- [性能基准](#九性能基准)
- [通用化适配](#十通用化适配)
- [常见问题](#十一常见问题)
- [注意事项](#十二注意事项)
- [Pitfalls（实战踩坑）](#十三pitfalls实战踩坑记录)
- [工具兼容性](#十四工具兼容性)
- [可复用提示词](#十五可复用提示词)
- [变更日志](#十六变更日志)

---

## 一、问题背景

### 长期运行 Agent 的记忆瓶颈

Hermes Agent 在每轮对话中都会将 **Memory** 和 **User Profile** 注入系统提示词。随着配置、偏好、API 凭证和工作流规则的积累，这些内容可能占用高达 **80-90%** 的可用上下文窗口。

```
┌─────────────────────────────────────────────┐
│           系统提示词（固定）                  │
├─────────────────────────────────────────────┤
│  ██████████████████████████████████████████  │ ← Memory（80-90%）
│  █                                      █  │
│  █      实际对话空间所剩无几              █  │
│  █                                      █  │
│  ██████████████████████████████████████████  │
└─────────────────────────────────────────────┘
```

### 核心矛盾

> **AI 需要知道规则的存在，但不需要每轮都看到规则全文。**

翻译请求只占不到 5% 的对话，但完整翻译工具配置 100% 的时间都在加载——这是一个典型的资源错配问题。

---

## 二、解决方案：三层记忆架构

### 2.1 核心原则

将信息按性质分为三层：

```
┌─────────────────────────────────────────────┐
│  第一层：用户规则（MEMORY + USER PROFILE）    │ ← 每轮注入，成本最高
│  仅限用户明确规定的偏好和约束                  │
├─────────────────────────────────────────────┤
│  第二层：对话记忆（外部文档）                  │ ← 按需读取，成本中等
│  内容、事件、项目、系统配置                    │
├─────────────────────────────────────────────┤
│  第三层：原始记录（会话搜索）                  │ ← 需要时搜索，成本最低
│  原始对话文本、调试日志                        │
└─────────────────────────────────────────────┘
```

### 2.2 优化效果

```
优化前                                优化后
┌─────────────────────────┐          ┌─────────────────────────┐
│█████████████████████████│ Memory   │██████████████           │ Memory
│█████████████████████████│ 80-90%   │██████████████           │ 25-35%
│                         │          │                         │
│███                      │ 对话空间  │░░░░░░░░░░░░░░░░░░░░░░░░│ 对话空间
│                         │          │░░░░░░░░░░░░░░░░░░░░░░░░│ 大幅增加
└─────────────────────────┘          └─────────────────────────┘
```

### 2.3 与 Hermes 内置功能的协同

AMIP 并非替代 Hermes 的内置记忆系统，而是在其之上构建的优化层：

| Hermes 功能 | AMIP 中的角色 |
|-------------|--------------|
| `memory()` 工具 | 管理第一层索引（MEMORY 条目的增删改） |
| `session_search()` | 提供第三层检索（历史会话的 FTS5 搜索） |
| Skills 系统 | 编码 AMIP 本身的流程和 Pitfalls |
| Cron Jobs | 定期执行文档同步和索引维护任务 |
| `/goal`、`/snapshot` | 跨轮次任务管理，不影响记忆层 |
| Delegation (子代理) | 子代理无父级记忆，需通过 context 传递信息 |

---

## 三、评估框架

### 3.1 五个评估维度

| 维度 | 问题 | 权重 |
|------|------|------|
| **频率** | 多久使用一次？每轮/每周/偶尔/仅一次 | ★★★ |
| **稳定性** | 会变化吗？永久/长期/短期/临时 | ★★★ |
| **工具影响** | 遗忘后是否导致选错工具或路径？ | ★★ |
| **纠错成本** | 用户是否需要重复纠正？ | ★★ |
| **可发现性** | 能否通过其他方式快速找到？ | ★ |

### 3.2 决策树

```
开始
│
├─ 是否为用户明确规定的规则/偏好？
│  ├─ 是 → MEMORY / USER PROFILE
│  └─ 否 ↓
│
├─ 是否影响「每轮对话的工具选择」？
│  ├─ 是 → MEMORY（系统路径、工具列表）
│  └─ 否 ↓
│
├─ 是否「跨会话引用、版本化、周期性需要」？
│  ├─ 是 → 外部文档 + MEMORY 指针
│  └─ 否 ↓
│
├─ 是否为「一次性任务的结果」？
│  ├─ 是 → 会话搜索（不存储）
│  └─ 否 ↓
│
└─ 默认 → 外部文档
```

### 3.3 快速分类表

| 信息类型 | 归属 | 示例 |
|----------|------|------|
| 用户下载偏好 | MEMORY（索引）→ Craft「偏好设置」（详情） | 离线部署包、国内镜像优先 |
| 用户输出风格 | MEMORY（索引）→ Craft「偏好设置」（详情） | 简洁、文学风格、技术写作规范 |
| 用户身份 | USER PROFILE（长期特质，避免易变信息） | 姓名、职业、兴趣 |
| 安装路径、端口 | Craft「偏好设置」 | 程序路径、服务端口 |
| API 凭证 | 环境变量 + Craft「偏好设置」（引用变量名） | 密钥、AppID |
| 工具启用/禁用状态 | Craft「偏好设置」 | 某工具已禁用、替代方案 |
| 活跃项目状态 | Craft「长期记忆」 | 当前版本、进度追踪 |
| 工作流详情 | Craft「偏好设置」 | 处理策略、流程步骤 |
| 已完成任务 | 会话搜索 | 某次翻译、某次格式转换 |
| 临时调试信息 | 会话搜索 | 错误日志、测试结果 |

### 3.4 USER PROFILE 策略

USER PROFILE 中的条目应遵循「长期稳定性」原则：

- ✅ **保留**：姓名、身份角色（如"高中生"）、写作风格、Token 偏好
- ❌ **避免**：具体年级/班级（每年变化）、短期角色（如某次活动的组委）、语言能力描述（对对话影响小）
- **原则**：概括化描述（"学生" > "高二（9）班"），减少因时间推移导致的维护成本

---

## 四、检索机制

### 4.1 检索优先级

```
用户提到某件事
│
├─ MEMORY/USER PROFILE 中有记录？
│  ├─ 是 → 直接使用（已在上下文中）
│  └─ 否 ↓
│
├─ 外部文档中有记录？
│  ├─ 是 → 读取文档，作为事实依据
│  └─ 否 ↓
│
├─ 会话搜索关键词
│  ├─ 找到 → 提取信息，判断是否值得沉淀到文档
│  └─ 未找到 → 告知用户无记录
```

### 4.2 冲突处理

当外部文档与会话搜索结果矛盾时：
- 以文档为准（因为是经过整理的）
- 但向用户说明差异，由用户确认

### 4.3 会话搜索的局限性

`session_search()` 基于 SQLite FTS5 全文检索，需注意：

- **中文分词**：FTS5 对中文的分词支持有限，模糊匹配可能漏召回。建议使用关键词而非完整句子
- **跨 Profile**：不同 Hermes Profile 的会话数据库独立，需要指定 `profile` 参数
- **仅限历史**：当前会话的未持久化内容无法搜索

---

## 五、沉淀机制

### 5.1 自动沉淀条件

满足以下任一条件即沉淀到外部文档：

- 用户明确要求记住
- 项目跨越 2+ 个会话
- 产生了可复用的工作成果（文件、配置、方案）
- 发现了用户偏好或规则

### 5.2 会话结束检查清单

| 检查项 | 更新内容 |
|--------|----------|
| 新的活跃项目？ | 更新项目列表 |
| 配置变更？ | 更新系统配置 |
| 新文件产出？ | 更新文件索引 |
| 值得记录的对话？ | 追加对话历史 |
| 新的用户规定？ | 更新用户规则 |

### 5.3 Craft 文档同步规则

- 保持 RIKO 文件夹中 **恰好 2 个文档**（偏好设置 + 长期记忆）
- 用户在 Craft 中手动编辑文档后，下次对话自动读取最新内容
- MEMORY 中仅保留指针索引，不内联详情

---

## 六、实施指南

### 第一步：盘点

列出所有 Memory 和 User Profile 条目，用五个维度评估。

### 第二步：创建外部文档

```
外部文档结构（以 Craft 为例）
├── 偏好设置                    ← 配置、API、工作流详情
│   ├── Dashboard配置
│   ├── SSH/远程机器
│   ├── Provider配置
│   ├── API凭证与外部服务
│   ├── 工作流详情
│   ├── 下载与部署偏好
│   ├── 输出与沟通偏好
│   └── 复习资料索引
│
└── 长期记忆                    ← 项目、产出、会话索引
    ├── Output文件夹总览
    └── 会话索引（按主题）
```

> **为什么用双文档而非单文档：**
> - 偏好设置变更频繁（配置、API），长期记忆相对稳定（历史、索引）
> - 双文档结构更清晰，避免单文档过长导致读取成本上升
> - Craft MCP 支持按文档读取，双文档可独立加载

> ⚠️ **注意**：「用户身份」不放在外部文档中——它属于 USER PROFILE（系统自动注入），放在 Craft 中会造成重复和不同步。

### 第三步：迁移条目

```diff
# 优化前（在 MEMORY 中，160 字符）
- Dashboard 配置：systemd 服务 dashboard.service（端口 8080），
  Profile 路径 ~/.hermes/profiles/user2/。

# 优化后（在外部文档中，MEMORY 仅保留指针）
+ 系统配置详情：Dashboard/服务/工作流 → Craft「偏好设置」[→ block:xxx]
```

### 第四步：验证

- [ ] Memory 占比是否降到目标（<35%）？
- [ ] 所有用户规则是否完整保留？
- [ ] 外部文档是否可通过指针访问？
- [ ] 会话搜索是否可用于历史查询？

---

## 七、索引格式

### 7.1 MEMORY 指针格式

```
Craft「<文件夹名>」文件夹仅<N>个文档——<文档1名称>（<内容摘要>）、<文档2名称>（<内容摘要>）。系统MEMORY仅保留索引，详情读Craft。
```

**示例：**

```
Craft「RIKO」文件夹仅2个文档——偏好设置（配置/API/工作流详情）、长期记忆（Output总览+会话索引）。系统MEMORY仅保留索引，详情读Craft。
```

### 7.2 用户规则格式

```
<规则名称>：<具体要求>
```

### 7.3 引用格式约定

| 引用类型 | 格式 | 说明 |
|----------|------|------|
| Craft 文档 | `[→ block:BLOCK_ID]` | 自定义约定，非 Craft 原生协议 |
| 本地文件 | `[→ ~/.hermes/config/file.md]` | 完整绝对路径 |
| 环境变量 | `见环境变量 VAR_NAME` | 凭证不内联 |

---

## 八、外部文档模板

<details>
<summary><b>文档一：偏好设置</b></summary>

```markdown
## Dashboard配置
- 服务名称：systemd 服务名，端口
- Profile 映射：default=User1（端口 X），user2=User2（端口 Y）

## SSH/远程机器
- 机器名：IP，端口，用户
- 密码：见环境变量 XXX_PASSWORD

## Provider配置
- 提供商名称：特性说明

## API凭证与外部服务
### 服务名称
- 凭证：见环境变量 XXX_API_KEY
- 路径：/path/to/tool/
- 快捷命令：command_name
- 用法：command "text" [options]

## 工作流详情
- 工作流名称：步骤说明

## 下载与部署偏好
- 偏好说明

## 输出与沟通偏好
- Token 节约规则
- 文件处理规则
```

</details>

<details>
<summary><b>文档二：长期记忆</b></summary>

```markdown
## Output文件夹总览（N个文件）
**位置**：/path/to/Output/
### 类别一
- 文件名 — 说明
### 类别二
- 文件名 — 说明

## 会话索引（按主题）
### 主题一
- **事件名**（日期）：摘要
### 主题二
- **事件名**（日期）：摘要
```

</details>

---

## 九、性能基准

### 实际优化结果（2026-06-14 实测）

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| Memory 条目数 | 18 | 7 | **-61%** |
| Memory 占用率 | 60% | 27% | **-55%** |
| User Profile 条目数 | 8 | 7 | -12.5% |
| User Profile 占用率 | 26% | 23% | -12% |
| 外部文档数 | 5 | 2（双文档） | -60% |
| 每轮固定 Token | ~2,670 字符 | ~1,205 字符 | **-55%** |

### 延迟影响

| 操作 | 延迟 | 说明 |
|------|------|------|
| Memory 查找 | 0ms | 已在上下文中 |
| 外部文档读取 | ~100ms | Craft MCP 调用 |
| 会话搜索 | ~200ms | SQLite FTS5 搜索 |
| 总开销 | ~100ms | 可忽略不计 |

---

## 十、通用化适配

### 10.1 适用条件

此模式适用于任何具备以下条件的 Agent：

1. **持久化记忆** —— 注入上下文的配置/规则
2. **外部文档读取** —— 文件系统或数据库访问
3. **搜索能力** —— 历史会话检索

### 10.2 通用实现

```python
class ThreeTierMemory:
    def __init__(self):
        self.user_rules = {}      # 第一层：始终加载
        self.conversation = {}    # 第二层：按需加载
        # 第三层：搜索时使用
    
    def add_rule(self, rule_id, content):
        """用户规则 → 第一层"""
        self.user_rules[rule_id] = content
    
    def add_conversation(self, key, content):
        """对话内容 → 第二层"""
        self.conversation[key] = content
    
    def get_context(self, user_input):
        """从适当层级构建上下文"""
        context = list(self.user_rules.values())
        for key, content in self.conversation.items():
            if key in user_input:
                context.append(content)
        return context
```

### 10.3 平台适配

<details>
<summary><b>本地文件方案</b></summary>

```
~/.hermes/config/
├── conversation-memory.md    # 对话记忆
├── api-services.md           # API 凭证、外部服务
└── workflow-preferences.md   # 工作流、用户偏好
```

Memory 指针格式：
```
对话记忆：~/.hermes/config/conversation-memory.md [详情见该文件]
```

</details>

<details>
<summary><b>数据库方案</b></summary>

```python
import sqlite3

class DatabaseMemory:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                key TEXT PRIMARY KEY,
                content TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def get(self, key):
        cursor = self.conn.execute(
            "SELECT content FROM conversation_memory WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    def set(self, key, content):
        self.conn.execute(
            "INSERT OR REPLACE INTO conversation_memory (key, content) VALUES (?, ?)",
            (key, content)
        )
        self.conn.commit()
```

</details>

---

## 十一、常见问题

<details>
<summary><b>Q: 外部文档不存在怎么办？</b></summary>

首次使用时创建，后续增量更新。Agent 检测到路径无效时提示用户重建。

</details>

<details>
<summary><b>Q: 如何处理频繁变化的凭证？</b></summary>

仅存储在外部文档中。凭证变更时更新文档，无需修改 Memory。实际凭证值写入 `.env`，文档中仅引用变量名。

</details>

<details>
<summary><b>Q: 我可以手动修改文档中的内容吗？</b></summary>

当然可以！文档可以让您直观地看到记忆的内容。更新文档后，下次对话会自动注入新的内容。

</details>

<details>
<summary><b>Q: 能否使用云存储？</b></summary>

可以！任何可访问的路径都适用：
- 本地文件：`~/.hermes/config/memory.md`
- 网络挂载：`/mnt/nas/hermes-config/memory.md`
- 云同步：`~/Dropbox/hermes-config/memory.md`
- 笔记平台：Craft MCP、Notion、Obsidian

</details>

<details>
<summary><b>Q: 外部文档太多怎么办？</b></summary>

保持 2-3 个文档为佳。当前实践采用双文档：「偏好设置」+「长期记忆」。

</details>

<details>
<summary><b>Q: 子代理（Delegation）能访问记忆吗？</b></summary>

不能直接访问。子代理运行在独立会话中，没有父级的 MEMORY 和 USER PROFILE。需要通过 `context` 参数传递相关信息。

</details>

---

## 十二、注意事项

1. **用户规则是核心**：Memory 只放用户明确规定的规则，不放系统发现的环境信息
2. **双文档结构**：偏好设置（配置/API/工作流）+ 长期记忆（历史/索引），保持 2-3 个文档为佳
3. **指针要准确**：Memory 中的指针必须指向正确的文档标识
4. **渐进迁移**：不必一次做完，可分批迁移，每批验证后再继续
5. **会话结束检查**：重要会话结束后自动更新文档，保持信息新鲜
6. **冲突以文档为准**：文档是整理过的，会话搜索是原始的
7. **敏感信息环境变量化**：API 密钥、密码等写入 `.env`，文档中只引用变量名
8. **工具存在性验证**：在 Memory 中记录工具之前，必须验证工具实际存在（`which <command>`）
9. **不要过度拆分文件**：按类别分文件（4-6 个），不要一个条目一个文件

---

## 十三、Pitfalls（实战踩坑记录）

### 13.1 `memory()` 工具精确匹配问题

`memory(action="remove"/"replace")` 需要精确子串匹配。部分条目即使文本看起来正确也可能匹配失败。

**原因：** 条目可能在存储时被截断、格式化，或包含不可见字符。

**解决方案：**
1. 使用较短的唯一子串（10-20 字符）作为 `old_text`
2. 如果多次失败，尝试更短的匹配字符串
3. 最后手段：用 `memory(action="add")` 添加新条目

### 13.2 行为触发规则 ≠ 工具索引

知道工具存在 ≠ 知道什么时候用。

```
# ❌ 只有工具索引
本地工具集：bt（翻译）、baidu_ocr（OCR）

# ✅ 工具索引 + 行为触发规则
本地工具集：bt（翻译）、baidu_ocr（OCR）
图片处理：收到含文字图片时优先用baidu_ocr提取文字，纯视觉用vision_analyze
```

### 13.3 批量操作效率

Memory 工具一次只能操作一条 entry。大量迁移时（15+ 条目）：
- 用 `replace` 更新现有条目（省去 remove + add 两步）
- 合并同类别条目为一条
- 合并后再加引用链接

### 13.4 Craft MCP API 陷阱

| 陷阱 | 说明 |
|------|------|
| `blocks update --id <rootBlockId>` | 会改变**页面标题**，而非块内容 |
| `blocks delete --id <rootBlockId>` | 会失败，应使用 `documents delete` |
| 无 `folders rename` | 使用 `folders update --name` 代替 |
| 分页游标失效 | 写操作后，之前的游标可能无效 |

### 13.5 迁移后验证清单

- [ ] 触发已迁移规则的场景 → Agent 是否正确执行？
- [ ] 问"你的 XX 配置是什么？" → 能否从详情文件拉取？
- [ ] 问"我有什么偏好？" → 能否列出所有索引条目？
- [ ] Memory 占用是否降到 35% 以下？

---

## 十四、工具兼容性

| 工具 | 用途 | 示例 |
|------|------|------|
| `mcp_craft_craft_read` | 读取 Craft 文档内容 | `blocks get <rootBlockId> --format markdown` |
| `mcp_craft_craft_write` | 写入/更新 Craft 文档 | `blocks add --id <pageId> --markdown "内容"` |
| `memory` | 管理系统 MEMORY 索引 | `memory(action="replace", content="新索引")` |
| `read_file` / `write_file` / `patch` | 本地文件操作 | `read_file("/path/to/file")` |
| `session_search` | 搜索历史会话 | `session_search(query="关键词")` |

---

## 十五、可复用提示词

<details>
<summary><b>一键复制的 Memory 优化提示词模板</b></summary>

> 请优化我的 Memory 结构，采用「Advanced Memory Index Pattern (AMIP)」：
>
> **评估标准**
> - ≤50 字符且高频使用：直接保留
> - 50-150 字符：压缩为一句话摘要
> - \>150 字符：迁移到外部文档，Memory 仅保留索引
> - 系统关键信息（路径/端口/工具状态）：保留原文
> - 易变信息（年级/班级/短期角色）：概括化或移除
>
> **操作步骤**
> 1. 列出当前所有 Memory 和 User Profile 条目，报告字符数
> 2. 创建双文档结构（偏好设置 + 长期记忆）
> 3. 对需要迁移的条目：写入文档 → 压缩 Memory 为 `规则摘要 [→ block:ID]`
> 4. 保留系统关键条目原文
> 5. 验证每个引用的路径/ID 是否正确
> 6. 完成后报告优化效果
>
> 目标：Memory 占用降到 30% 以下，保持所有规则的可发现性。

</details>

---

## 十六、变更日志

### v3.1.0（2026-06-14）
- **重大变更：** 更名为 Advanced Memory Index Pattern (AMIP)
- **新增：** Pitfalls 章节，整合实战踩坑
- **新增：** USER PROFILE 策略章节
- **新增：** 与 Hermes 内置功能的协同表
- **新增：** 会话搜索的局限性说明
- **新增：** 子代理与记忆的关系说明
- **新增：** 可复用提示词章节
- **更新：** 性能基准为实测值（Memory 27%、Token -55%）

### v3.0.0（2026-06-13）
- **重大变更：** 双文档结构（偏好设置 + 长期记忆）
- **重大变更：** Craft MCP 作为存储后端
- **新增：** 工具兼容性章节
- **新增：** 敏感信息环境变量化规则

### v2.0.0（2026-06-13）
- **重大变更：** 三层架构替代两层
- **新增：** 五维评估框架 + 决策树

### v1.0.0（2026-06-12）
- 初始发布

---

<div align="center">

**问题？** [提交 Issue](https://github.com/elder-plinius/CL4R1T4S/issues) 或加入 [Hermes Agent Discord](https://discord.gg/hermes-agent)

**觉得有帮助？** Star 仓库并分享给其他 Hermes 用户！ ⭐

</div>
