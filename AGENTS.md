# AMIP — Advanced Memory Index Pattern

You are following the Advanced Memory Index Pattern (AMIP), a three-layer memory optimization strategy for long-running AI agents.

Core principle: **AI needs to know rules exist, but does not need to see the full text of every rule in every turn.**

## The Three Layers

1. **Layer 1 — User Rules (MEMORY / USER PROFILE):** Injected every round. Only explicit user preferences and constraints. Highest cost.
2. **Layer 2 — Conversation Memory (External Documents):** Read on demand. Configuration details, project status, workflows, API credential references. Medium cost.
3. **Layer 3 — Raw Records (Session Search):** Searched when needed. Historical conversations, debug logs, completed tasks. Lowest cost.

## Decision Tree

When deciding where to store information:

1. Is it a user-defined rule/preference? → **MEMORY / USER PROFILE**
2. Does it impact every-round tool choice? → **MEMORY** (system paths, tool lists)
3. Is it cross-session, versioned, or periodically needed? → **External Document + MEMORY pointer**
4. Is it a one-time task result? → **Session Search** (don't store)
5. Default → **External Document**

## Rules

- MEMORY only holds user-defined rules. Never bulk-load configuration details.
- External documents use a two-document structure: **Preferences** (config/API/workflows) + **Long-term Memory** (history/index).
- API credentials go in `.env`; documents reference variable names only.
- MEMORY pointers follow this format: `Craft「<folder>」仅<N>个文档——<doc1>（<summary>）、<doc2>（<summary>）。系统MEMORY仅保留索引，详情读外部文档。`
- Target: MEMORY footprint ≤35% of context window.
- Validate after migration: all user rules preserved, pointers valid, triggers still work.

## USER PROFILE Strategy

- ✅ Keep: Long-term stable traits (name, role, writing style, token preferences)
- ❌ Avoid: Frequently changing specifics (grade/year), short-term roles
- Principle: Generalized descriptions ("student" > "Grade 10 Class 9")

## Pitfalls

- `memory()` remove/replace requires exact substring match. Use short unique substrings (10-20 chars).
- Tool index ≠ behavior trigger. Record both: "tool exists" AND "when to use it."
- Sub-agents have no parent memory. Pass info via `context` parameter.
- Don't over-split files. 2-3 documents is optimal.
