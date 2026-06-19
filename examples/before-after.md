# AMIP Examples — Before / After

## Example 1: System Configuration

### Before (in MEMORY, ~320 chars)
```
Dashboard 配置：systemd 服务 dashboard.service（端口 8080），Profile 路径
~/.hermes/profiles/user2/。SSH 到 CASC-550C：IP 192.168.31.166，端口 22，
用户 RevE，密码见环境变量 CASC_PASSWORD。sing-box 代理：Trojan 订阅，
本地端口 127.0.0.1:7890，配置 ~/.hermes/sing-box/config.json，管理脚本
~/.local/bin/proxy（start/stop/status/test）。
```

### After (MEMORY ~90 chars + External Doc)
**MEMORY:**
```
系统配置详情（Dashboard/SSH/代理）→ Craft「偏好设置」[→ block:abc123]
```

**External Doc (Craft「偏好设置」):**
```markdown
## Dashboard配置
- 服务：systemd dashboard.service，端口 8080
- Profile：default=User1（端口 X），user2=User2（端口 Y）

## SSH/远程机器
- CASC-550C：192.168.31.166:22，用户 RevE
- 密码：见环境变量 CASC_PASSWORD

## 代理配置
- sing-box：Trojan 订阅，本地 127.0.0.1:7890
- 配置：~/.hermes/sing-box/config.json
- 管理：~/.local/bin/proxy (start/stop/status/test)
```

**Savings: ~230 chars (72%)**

---

## Example 2: Tool Configuration

### Before (in MEMORY, ~280 chars)
```
baidu_ocr：收到含文字的图片时调用，提取文字后再分析。手写内容用
handwriting端点（效果远优于general_basic），临时切换：sed替换脚本中
general_basic为handwriting。agent.image_input_mode设为manual，图片不
自动注入模型，由RIKO主动调用baidu_ocr提取文字后再分析。MiMo原生视觉
能力因区域限制不可用。百度OCR为含文字图片的首选工具。
```

### After (MEMORY ~120 chars)
**MEMORY:**
```
baidu_ocr：含文字图片首选工具，handwriting端点优于general_basic。
image_input_mode=manual，图片不自动注入，由Agent主动调用OCR提取文字。
```

**Savings: ~160 chars (57%)**

---

## Example 3: MEMORY Pointer Pattern

### Single-line pointer that encodes everything:
```
Craft「RIKO」文件夹仅2个文档——偏好设置（配置/API/工作流详情）、长期记忆
（Output总览+会话索引）。系统MEMORY仅保留索引，详情读Craft。
```

This single line replaces what would otherwise be 5-8 separate MEMORY entries containing full configuration details.

---

## Metrics

| Example | Before | After | Savings |
|---------|--------|-------|---------|
| System Config | 320 chars | 90 chars | 72% |
| Tool Config | 280 chars | 120 chars | 57% |
| User Profile | 200 chars | 120 chars | 40% |
| **Total** | **800 chars** | **330 chars** | **59%** |
