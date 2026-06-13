# Memory 索引模式

> **一种三层记忆优化策略，可将 Token 消耗降低 50% 以上，同时保留所有运行规则。**
>
> **当前实践**：外部文档采用双文档结构（偏好设置 + 长期记忆），存储于 Craft MCP 笔记平台。

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue)](https://hermes-agent.nousresearch.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 一、问题背景

### 长期运行 Agent 的记忆瓶颈

Hermes Agent 在每轮对话中都会将 **Memory** 和 **User Profile** 注入系统提示词。随着配置、偏好、API 凭证和工作流规则的积累，这些内容可能占用高达 **80-90%** 的可用上下文窗口，这无疑消耗大量 Token 且对运行速度产生严重影响。

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

**AI 需要知道规则的存在，但不需要每轮都看到规则全文。**

考虑一个典型的外部工具配置：

```yaml
# 这段 200 字符的配置每轮都注入，即使不需要翻译
- 工具：外部翻译 CLI
  路径：/opt/tools/translator/
  命令：translate "text" --to en
  API Key: sk-xxx...xxxx
  App ID: app-xxxxxxxxxxxx
  用法：translate "Hello world" → "你好世界"
  备注：支持 200+ 种语言，自动检测源语言
```

**现实**：翻译请求只占不到 5% 的对话，但完整配置 100% 的时间都在加载。

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
┌─────────────────────────────────────────────┐
│           系统提示词（优化后）                 │
├─────────────────────────────────────────────┤
│  ██████████████████                         │ ← Memory（30-40%）
│  ██ 仅用户规则 ██                            │
│  ██████████████████                         │
│                                             │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ ← 对话空间大幅增加
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────────────────────┘

外部文档（对话记忆）仅在需要时加载：
┌─────────────────────────────────────────────┐
│  read_file("对话记忆文档")                   │
│  → 完整配置、项目状态、历史记录               │
└─────────────────────────────────────────────┘
```

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
| 用户身份 | USER PROFILE 或 Craft「长期记忆」 | 姓名、职业、兴趣 |
| 安装路径、端口 | Craft「偏好设置」 | 程序路径、服务端口 |
| API 凭证 | 环境变量 + Craft「偏好设置」（引用变量名） | 密钥、AppID |
| 工具启用/禁用状态 | Craft「偏好设置」 | 某工具已禁用、替代方案 |
| 活跃项目状态 | Craft「长期记忆」 | 当前版本、进度追踪 |
| 工作流详情 | Craft「偏好设置」 | 处理策略、流程步骤 |
| 已完成任务 | 会话搜索 | 某次翻译、某次格式转换 |
| 临时调试信息 | 会话搜索 | 错误日志、测试结果 |

---

## 四、检索机制

### 4.1 检索优先级

```
用户提到某件事
│
├─ 外部文档中有记录？
│  ├─ 是 → 直接读取，作为事实依据
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

---

## 五、沉淀机制

### 5.1 自动沉淀条件

满足以下任一条件即沉淀到外部文档：
- 用户明确要求记住
- 项目跨越 2+ 个会话
- 产生了可复用的工作成果（文件、配置、方案）
- 发现了用户偏好或规则

### 5.2 会话结束检查清单

每次重要会话结束时，检查并更新外部文档：

| 检查项 | 更新内容 |
|--------|----------|
| 新的活跃项目？ | 更新项目列表 |
| 配置变更？ | 更新系统配置 |
| 新文件产出？ | 更新文件索引 |
| 值得记录的对话？ | 追加对话历史 |
| 新的用户规定？ | 更新用户规则 |

---

## 六、实施指南

### 第一步：盘点

列出所有 Memory 和 User Profile 条目，用五个维度评估。

### 第二步：创建外部文档

创建双文档结构（推荐使用 Craft MCP 或本地 Markdown 文件）：

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
└── 长期记忆                    ← 身份、项目、会话索引
    ├── 用户身份
    ├── Output文件夹总览
    └── 会话索引（按主题）
```

**为什么用双文档而非单文档：**
- 偏好设置变更频繁（配置、API），长期记忆相对稳定（身份、历史）
- 双文档结构更清晰，避免单文档过长导致读取成本上升
- Craft MCP 支持按文档读取，双文档可独立加载

### 第三步：迁移条目

对每条需要迁移的条目：

1. 将完整内容写入外部文档对应章节
2. 从 Memory 中删除原条目
3. 如需要，添加一行指针

**示例：**

```diff
# 优化前（在 MEMORY 中，160 字符）
- Dashboard 配置：systemd 服务 dashboard.service（端口 8080），
  Profile 路径 ~/.hermes/profiles/user2/。映射：default=User1（端口 8080），user2=User2（端口 8081）

# 优化后（在外部文档中，MEMORY 仅保留指针）
+ 系统配置详情：Dashboard/服务/工作流 → 对话记忆文档 [→ doc:xxx]
```

### 第四步：验证

- Memory 占比是否降到目标（<35%）？
- 所有用户规则是否完整保留？
- 外部文档是否可通过指针访问？
- 会话搜索是否可用于历史查询？

---

## 七、索引格式

### 7.1 MEMORY 指针格式

```
Craft「<文件夹名>」文件夹仅<N>个文档——<文档1名称>（<内容摘要>）、<文档2名称>（<内容摘要>）。系统MEMORY仅保留索引，详情读Craft。
```

示例：
```
Craft「RIKO」文件夹仅2个文档——偏好设置（配置/API/工作流详情）、长期记忆（用户身份+Output总览+会话索引）。系统MEMORY仅保留索引，详情读Craft。
```

### 7.2 用户规则格式

```
<规则名称>：<具体要求>
```

示例：
```
下载偏好：离线部署包优先，手动下载，国内镜像优先
文件处理规则：Word 转 PDF 使用宋体，英文使用 Times New Roman
```

---

## 八、外部文档模板（以 Craft MCP 实践为例）

### 8.1 双文档模板

#### 文档一：偏好设置

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

#### 文档二：长期记忆

```markdown
## 用户身份
- 全名：姓名
- 身份：职业/年级
- 特点：兴趣、技能

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

### 8.2 MEMORY 索引格式（当前实践）

```markdown
Craft「RIKO」文件夹仅2个文档——偏好设置（配置/API/工作流详情）、长期记忆（用户身份+Output总览+会话索引）。系统MEMORY仅保留索引，详情读Craft。
Craft文档同步规则：保持RIKO文件夹中2个文档的最新状态。用户编辑文档时同步更新。
```

---

## 九、性能基准

### 实际优化结果

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| Memory 条目数 | 18 | 7 | -61% |
| Memory 占用率 | 60% | 30% | -50% |
| User Profile 条目数 | 8 | 7 | -12.5% |
| User Profile 占用率 | 26% | 22% | -15% |
| 外部文档数 | 5 | 1（合并） | -80% |
| 每轮固定 Token | ~2,670 字符 | ~1,360 字符 | -49% |

### 延迟影响

| 操作 | 延迟 | 说明 |
|------|------|------|
| Memory 查找 | 0ms | 已在上下文中 |
| 外部文档读取 | ~100ms | 文件读取调用 |
| 会话搜索 | ~200ms | 数据库搜索 |
| 总开销 | ~100ms | 可忽略不计 |

---

## 十、通用化适配

### 10.1 适配其他 AI Agent

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
        context = list(self.user_rules.values())  # 始终包含用户规则
        
        # 添加相关对话记忆
        for key, content in self.conversation.items():
            if key in user_input:
                context.append(content)
        
        return context
```

### 10.3 平台适配示例

#### 本地文件方案

可使用 Craft 等支持 MCP 的笔记平台，亦可使用本地文件：

```
~/.hermes/config/
├── conversation-memory.md    # 对话记忆（对应第一层文档）
├── api-services.md           # API 凭证、外部服务
└── workflow-preferences.md   # 工作流、用户偏好
```

Memory 中的指针格式：
```
对话记忆：~/.hermes/config/conversation-memory.md [详情见该文件]
```

#### 数据库方案

对于大规模部署，可使用数据库：

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

---

## 十一、常见问题

### Q: 外部文档不存在怎么办？
**A:** 首次使用时创建，后续增量更新。Agent 检测到路径无效时提示用户重建。

### Q: 如何处理频繁变化的凭证？
**A:** 仅存储在外部文档中。凭证变更时更新文档，无需修改 Memory。

### Q: 我可以手动修改文档中的内容吗？
**A:** 当然可以！文档可以让您直观地看到记忆的内容。更新文档后，下次对话会自动注入新的内容。

### Q: 能否使用云存储？
**A:** 可以！任何可访问的路径都适用：
- 本地文件：`~/.hermes/config/memory.md`
- 网络挂载：`/mnt/nas/hermes-config/memory.md`
- 云同步：`~/Dropbox/hermes-config/memory.md`

### Q: 外部文档太多怎么办？
**A:** 保持 2-3 个文档为佳。当前实践采用双文档：「偏好设置」+「长期记忆」，分别存放配置/API 和身份/历史。

### Q: 与 Hermes 内置记忆工具兼容吗？
**A:** 完全兼容。使用 `memory(action="replace")` 更新索引条目，使用 `read_file()` 访问详情。

### Q: 如何处理需要索引和详情的规则？
**A:** 指针格式已包含详情路径：
```
触发条件 → 工具 [→ 详情文件路径]
```
Agent 仅在执行规则时读取详情文件。

---

## 十二、注意事项

1. **用户规则是核心**：Memory 只放用户明确规定的规则，不放系统发现的环境信息
2. **双文档结构**：偏好设置（配置/API/工作流）+ 长期记忆（身份/历史/索引），保持 2-3 个文档为佳
3. **指针要准确**：Memory 中的指针必须指向正确的文档标识
4. **渐进迁移**：不必一次做完，可分批迁移，每批验证后再继续
5. **会话结束检查**：重要会话结束后自动更新文档，保持信息新鲜
6. **冲突以文档为准**：文档是整理过的，会话搜索是原始的
7. **敏感信息环境变量化**：API 密钥、密码等写入 `.env`，文档中只引用变量名

---

## 十三、工具兼容性

### 13.1 Craft MCP 工具

本模式在 Hermes Agent 中通过以下工具实现：

| 工具 | 用途 | 示例 |
|------|------|------|
| `mcp_craft_craft_read` | 读取 Craft 文档内容 | `blocks get <rootBlockId> --format markdown` |
| `mcp_craft_craft_write` | 写入/更新 Craft 文档 | `blocks add --id <pageId> --markdown "内容"` |
| `memory` | 管理系统 MEMORY 索引 | `memory(action="replace", content="新索引")` |
| `read_file` | 读取本地文件 | `read_file("/path/to/file")` |
| `session_search` | 搜索历史会话 | `session_search(query="关键词")` |

### 13.2 Craft MCP 操作流程

#### 读取偏好设置
```python
# 1. 列出 RIKO 文件夹中的文档
mcp_craft_craft_read(command="documents list --folder <riko-folder-id>")

# 2. 读取偏好设置文档
mcp_craft_craft_read(command="blocks get <偏好设置-rootBlockId> --format markdown")
```

#### 更新偏好设置
```python
# 添加新内容到文档末尾
mcp_craft_craft_write(command="blocks add --id <pageId> --markdown '## 新章节\n- 内容'")

# 更新已有块
mcp_craft_craft_write(command="blocks update --id <blockId> --markdown '新内容'")
```

#### 更新 MEMORY 索引
```python
# 替换现有索引条目
memory(action="replace", old_text="旧索引", content="新索引")

# 添加新索引条目
memory(action="add", content="新规则：xxx")
```

### 13.3 工具调用保证

所有工具均可正常调用，无兼容性问题：

- ✅ `mcp_craft_craft_read` — 读取 Craft 文档
- ✅ `mcp_craft_craft_write` — 写入 Craft 文档
- ✅ `memory` — 管理系统 MEMORY
- ✅ `read_file` / `write_file` / `patch` — 本地文件操作
- ✅ `session_search` — 历史会话搜索
- ✅ `terminal` — 执行 shell 命令
- ✅ `web_search` / `web_extract` — 网络搜索
- ✅ `skill_view` / `skill_manage` — 技能管理
- ✅ `cronjob` — 定时任务
- ✅ `delegate_task` — 子任务委派

### 13.4 本地文件方案（备选）

如不使用 Craft MCP，可将文档存储在本地：

```
~/.hermes/config/
├── preferences.md      # 偏好设置
└── long-term-memory.md # 长期记忆
```

MEMORY 索引格式：
```
外部文档：~/.hermes/config/preferences.md（配置/API/工作流）
外部文档：~/.hermes/config/long-term-memory.md（身份/历史/索引）
```

读取方式：
```python
read_file("/home/user/.hermes/config/preferences.md")
```

---

## 十四、变更日志

### v3.0.0（2026-06-13）
- **重大变更：** 外部文档从单文档改为双文档结构（偏好设置 + 长期记忆）
- **重大变更：** 明确使用 Craft MCP 作为存储后端
- **新增：** 工具兼容性章节，列出所有可用工具及操作流程
- **新增：** 本地文件方案作为备选
- **新增：** 敏感信息环境变量化规则
- **更新：** 模板章节改为双文档模板
- **更新：** 注意事项中"单文档优于多文档"改为"双文档结构"

### v2.0.0（2026-06-13）
- **重大变更：** 三层架构（Memory + 外部文档 + 会话搜索）替代两层（Memory + 文件）
- **重大变更：** 两层分类（用户规则 + 对话记忆）替代评分系统
- **新增：** 五维评估框架替代三维评分
- **新增：** 外部文档与会话搜索协同机制
- **新增：** 自动沉淀规则
- **新增：** 会话结束检查清单
- **更新：** 通用化模板，移除个人案例
- **更新：** 性能基准数据
- **移除：** 评分决策矩阵（由决策树替代）

### v1.0.0（2026-06-12）
- 初始发布
- 核心评估评分系统（三维）
- 四个详情文件模板
- 迁移示例
- 性能基准

---

**问题？** 提交 Issue 或加入 [Hermes Agent Discord](https://discord.gg/hermes-agent)。

**觉得有帮助？** Star 仓库并分享给其他 Hermes 用户！
