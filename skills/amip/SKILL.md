---
name: amip
description: >
  Advanced Memory Index Pattern — three-layer memory optimization for long-running
  AI Agents. Reduces token overhead by 55% by splitting information into: Layer 1
  (user rules, injected every round), Layer 2 (external docs, read on demand),
  Layer 3 (session search, searched when needed). Use when user says "optimize memory",
  "memory too long", "AMIP", or when MEMORY exceeds 50% of context window.
version: 4.0.0
license: MIT
---

# AMIP — Advanced Memory Index Pattern

Core principle: **AI needs to know rules exist, but does not need to see the full text of every rule in every turn.**

## When to Activate

- MEMORY occupies >50% of context window
- User says "optimize memory", "memory too long", "compress memory", "AMIP"
- MEMORY has >15 entries
- First-time Hermes setup (recommend adopting early)

## Three-Layer Architecture

```
Layer 1: User Rules (MEMORY + USER PROFILE)  ← injected every round, highest cost
  Only explicit user preferences and constraints

Layer 2: Conversation Memory (External Docs)  ← read on demand, medium cost
  Config details, project status, workflows, API credential references

Layer 3: Raw Records (Session Search)         ← searched when needed, lowest cost
  Historical conversations, debug logs, completed tasks
```

## Five-Dimension Evaluation

Score each MEMORY/Profile entry (1-3★):

| Dimension | Question | Weight |
|-----------|----------|--------|
| **Frequency** | How often used? every round / weekly / occasionally / once | ★★★ |
| **Stability** | Will it change? permanent / long-term / short-term / temporary | ★★★ |
| **Tool Impact** | Forgetting → wrong tool or path? | ★★ |
| **Correction Cost** | User must repeat correction? | ★★ |
| **Discoverability** | Can it be found quickly another way? | ★ |

## Decision Tree

```
Is it a user-defined rule/preference?
├─ Yes → MEMORY / USER PROFILE
└─ No ↓

Does it impact every-round tool choice?
├─ Yes → MEMORY (system paths, tool lists)
└─ No ↓

Is it cross-session, versioned, or periodically needed?
├─ Yes → External Doc + MEMORY pointer
└─ No ↓

Is it a one-time task result?
├─ Yes → Session Search (don't store)
└─ No → Default → External Doc
```

## Quick Classification

| Information Type | Belongs To | Example |
|-----------------|------------|---------|
| User preferences/rules | MEMORY | Token saving, output style, file rules |
| User identity | USER PROFILE | Name, role, interests (avoid volatile info) |
| Config / API / workflow details | External Doc | Program paths, ports, tool usage |
| API credentials | .env + External Doc reference | Keys, AppID |
| Active project status | External Doc | Current version, progress |
| Completed tasks | Session Search | A specific translation, a format conversion |
| Temporary debug info | Session Search | Error logs, test results |

## Implementation Steps

### Step 1: Audit
List all MEMORY and User Profile entries. Score each with the five dimensions.

### Step 2: Create External Docs
Use a **two-document structure** (store in Craft / local files / any accessible path):

**Doc 1: Preferences** — Config, API, workflows, download preferences, output preferences
**Doc 2: Long-term Memory** — Output folder overview, session index by topic

### Step 3: Migrate Entries
```
# Before (in MEMORY, 160 chars)
Dashboard config: systemd service dashboard.service (port 8080)...

# After (MEMORY retains pointer only)
System config: Dashboard/services/workflow → Craft「Preferences」[→ block:xxx]
```

### Step 4: Validate
- [ ] Memory footprint ≤35%?
- [ ] All user rules preserved?
- [ ] External docs accessible via pointer?
- [ ] Triggers for migrated rules still work?

## MEMORY Pointer Format

```
Craft「<folder>」仅<N>个文档——<doc1>（<summary>）、<doc2>（<summary>）。系统MEMORY仅保留索引，详情读外部文档。
```

Local file alternative:
```
<rule name>详情：~/.hermes/config/<filename>.md
```

## USER PROFILE Strategy

- ✅ Keep: Name, role, writing style, token preferences
- ❌ Avoid: Grade/year (changes annually), short-term roles, language proficiency
- Principle: Generalized ("student" > "Grade 10 Class 9")

## Pitfalls

### `memory()` Exact Matching
`memory(action="remove"/"replace")` needs exact substring. Use short unique substrings (10-20 chars). If repeated failures, use `add` instead.

### Behavior Trigger ≠ Tool Index
```
❌ Local tools: bt (translate), baidu_ocr (OCR)
✅ Local tools: bt (translate), baidu_ocr (OCR)
   Image handling: text-heavy images → baidu_ocr first; pure vision → vision_analyze
```

### Batch Operation Efficiency
For 15+ entries: use `replace` (saves remove + add), merge same-category entries into one.

### Don't Over-Split Files
Group by category (4-6 files), not one file per entry.

### Sensitive Info → Environment Variables
API keys, passwords in `.env`; documents reference variable names only.

### Sub-agents Have No Memory
Sub-agents run in isolated sessions. Pass info via `context` parameter.

## Performance Benchmarks

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Memory entries | 18 | 7 | -61% |
| Memory footprint | 60% | 27% | **-55%** |
| Per-round fixed tokens | ~2,670 chars | ~1,205 chars | **-55%** |

## Reusable Prompt Template

> Please optimize my Memory structure using AMIP:
>
> **Evaluation criteria**
> - ≤50 chars & high frequency: keep as-is
> - 50-150 chars: compress to one-line summary
> - >150 chars: migrate to external doc, MEMORY keeps pointer only
> - System-critical info (paths/ports/tool status): keep verbatim
> - Volatile info (grade/class/short-term role): generalize or remove
>
> **Steps**
> 1. List all MEMORY and User Profile entries with char counts
> 2. Create two-doc structure (Preferences + Long-term Memory)
> 3. For migration candidates: write to doc → compress MEMORY to index pointer
> 4. Keep system-critical entries verbatim
> 5. Verify all path/ID references are correct
> 6. Report optimization results
>
> Target: Memory footprint ≤30%, all rules discoverable.
