---
name: pyu-harness-setup-generic
description: Bootstrap a self-enforcing harness system (blueprint + CHANGELOG + Facts/current-status + KB + rules) for a new research project. ENV-AGNOSTIC skeleton — adapts to 4 project archetypes (exploration / reproduction / experimentation / dataset). MANDATORY first step — trigger /oh-my-claudecode:deep-interview to clarify project goal, scope, and project-type before scaffolding.
argument-hint: "[--at <target_dir>] [project description]"
trigger_keywords: [pyu-harness-setup, new project harness, harness setup, setup harness for, 起 harness, 新项目 harness]
---

# pyu-harness-setup-generic — Project Harness Bootstrap (environment-agnostic)

> **Use when**: 一个**新**项目 / 新 worktree 需要 setup 一套"自动维护 long-run context + 知道 current status + 历史追踪"的 harness 系统。
> **Do NOT use when**: 项目已有 `blueprint.md` + `CHANGELOG.md` + `.claude/rules/`（已有 harness，直接用）。
> **Env-coupled variant**: 如果你在 CoreWeave SLURM cluster + conda env `imp_genai` 上工作，直接用 `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/`（含 partition / shared paths / conda 约定）。本通用版**不假定**任何集群或 conda env。

---

## §0 What this skill produces

**5 个机制互锁的闭环**（与运行环境无关）：

1. **Self-injecting** — Rule auto-fire（matcher / trigger_keywords / SessionStart hook）
2. **Self-naming** — Rule §0 列出 mandatory tail/cat 路径；这些路径都被 skill 创建
3. **Self-explaining** — 每个 artifact 顶部自述契约（"How to use this file"）
4. **Self-checking** — KB sync script + gitignore boundary 主动屏蔽错误状态
5. **Self-recording** — CHANGELOG append-only + Facts/current-status 验证状态

---

## §1 MANDATORY: Trigger /deep-interview first

接到本 skill invoke，**第一步**调 `Skill("oh-my-claudecode:deep-interview")` 把以下 8 个核心 ambiguity 问清楚。**不允许跳过**。

### 8 个 mandatory clarification 问题（环境无关）

1. **Project archetype** ★ 决定整套 scaffold 形态
   - (a) **Exploration**：survey SOTA / 跑别人 method / 决定方向
   - (b) **Reproduction**：复现一篇 paper / 一套 baseline
   - (c) **Active experimentation**：已有 model，跑大量 ablation
   - (d) **Dataset construction**：从 raw data 构造 / 验证 dataset
   - (e) **Mixed**：(a) + (c) 等组合

2. **Module placement**
   - (i) **Standalone repo** at `<workspace>/<project>/`
   - (ii) **Worktree of monorepo**
   - (iii) **Module within an existing worktree** at `<worktree>/<area>/<module>/`

3. **Long-term goal** — 一句话定义"项目跑完算成功"是什么？必须可写进 blueprint Mission。

4. **Time horizon** — 几周 / 几月 / 长期？决定 `current-status.md` 是否需要。
   - < 2 周 → 不需要 current-status，CHANGELOG `[unreleased]` 够
   - 2 周–3 月 → 需要 current-status.md（live snapshot）
   - > 3 月 + 多 ablation 集中 → 需要 SessionStart hook 自动注入 current-status

5. **Knowledge base scope** — 是否需要 paper KB？
   - 不需要 → 跳过 KnowledgeBase
   - 需要 → 哪些 topics 在 scope？数据源在哪（obsidian vault / 内嵌 / 外部）？

6. **External reference repos** — 是否要 `<reference>/` 风格的只读 clone 区？
   - exploration / reproduction 通常需要
   - active experimentation 通常**不**需要

7. **Verified facts 存储** — single-file 还是 dir？
   - 验证过的 fact 少且杂 → `Facts.md` (single file)
   - 按主题积累很多 atomic claim → `facts/<topic>.md` dir

8. **Compute intensity** — 是否长跑 batch job？是否需要 wandb / tensorboard log 在 `logs/`？是否需要 SLURM/cluster-specific 配置？
   - 若是 → 提示 user 参考 `optional/cluster-snippets/` 下的 cluster-specific 模板

deep-interview 收敛到 ambiguity ≤ 20% 后才允许进 scaffold。

---

## §2 Architecture: 4 archetypes ↔ 模板差异

每个 archetype 对应**一组**变体。Skill 根据 deep-interview 答案选模板。

### Archetype A — Exploration

**特征**：未知数大，先看别人怎么做，后决定路径

```
<root>/
├── blueprint.md             ← Mission + Open Questions 重 / Decisions 轻
├── CHANGELOG.md             ← Decisions / Failures / Lessons / Open Questions
├── Facts.md                 ← single file（早期 fact 少）
├── docs/
│   ├── repo-structure.md    ← where-does-it-go
│   ├── workflow.md
│   └── harness.md
├── KnowledgeBase/           ← 选择性 symlink（vault / 内嵌）
│   ├── topics/<4-6 topic>.md
│   ├── <PaperName>/         ← per-paper symlink
│   └── scripts/{check_kb_sync.sh, refresh_kb.sh}
├── <reference-gallery>/     ← 只读参考 clone 区（archetype A 必备）
│   ├── .gitignore (* + !README.md)
│   └── README.md (clone list)
├── scripts/                 ← 主代码
├── viewer/                  ← 可视化
└── 0_debug/                 ← 临时输出（.gitignore'd）
```

**Rules**: `<project>.md` (主) + `knowledge-base.md` + `<compute>.md` (若长跑 batch job) + `github-workflow.md` (若 monorepo worktree)

### Archetype B — Reproduction

**特征**：明确 paper，明确 SOTA target，分阶段验证

```
<root>/
├── blueprint.md             ← Decisions 重，Architecture 明确，sub-blueprint 可拆
├── CHANGELOG.md
├── docs/
│   ├── papers/<PaperName>/  ← 主要参考 paper KB（per-paper folder）
│   ├── model-arch/          ← 每个模型组件 deep-dive
│   ├── data/                ← 数据格式 deep-dive
│   ├── training/            ← 训练机制 deep-dive
│   ├── archive/             ← 弃用文档（不删，留 context）
│   ├── repo-structure.md
│   ├── workflow.md
│   └── harness.md
├── experiments/             ← per-run journal
├── model/blueprint.md       ← 子模块级 sub-blueprint
├── external/                ← 只读 reference repos
├── community_versions/      ← 社区复现对比
└── scripts/ / configs/ / lightning/ / losses/ / metrics/ ...
```

**Rules**: `<module>.md` (主) + `knowledge-base.md` + `evaluation-<topic>.md` + `<compute>.md` + `github-workflow.md`

### Archetype C — Active Experimentation

**特征**：已有 model，多 ablation 同时跑，需要 cross-experiment snapshot

```
<root>/
├── blueprint.md
├── CHANGELOG.md
├── current-status.md        ← ★ 跨实验 live snapshot（archetype C 必备）
├── docs/
├── experiments/             ← 多 ablation 子目录，per-run result.md
│   ├── ablation-v1/
│   ├── ablation-v2/
│   ├── aggregate_eval.py
│   └── _summary_plots.py
├── knowledge-base/          ← 项目内 KB
├── src/                     ← 主 model 代码
├── batch-jobs/              ← per-experiment batch templates (sbatch / k8s yaml / etc.)
├── eval/ / eval-set/        ← 评估代码 + 评估数据
├── logs/
└── reference/               ← 别人代码（如果有）
```

**Rules**: `<project>.md` (主，明示 SessionStart hook inject current-status)
**Hooks**: `.claude/hooks/session_start_inject.sh` 必备 — auto-tail CHANGELOG + auto-cat current-status

### Archetype D — Dataset Construction

**特征**：从 raw data 构造数据集，多 atomic verified fact

```
<root>/
├── blueprint.md
├── CHANGELOG.md
├── docs/
│   ├── structure.md         ← live folder map
│   └── deferred/            ← known-but-not-yet-done
├── facts/                   ← ★ 主题分 file（archetype D）
│   ├── <topic-1>.md
│   ├── <topic-2>.md
│   └── README.md
├── knowledge/               ← 内嵌 paper / topic
├── 0_debug/                 ← 中间产物、smoke test 输出
├── scripts/                 ← 主代码
│   ├── tmp-debug/
│   └── <main>.<batch-ext>
├── refer_datasets/          ← 外部 dataset 引用（.gitignore data）
└── <data-source>/           ← 项目主要数据源 dir
```

**Rules**: 7 个细粒度 rule：
- `session-start-mandatory-read.md`
- `0-debug-output.md`
- `changelog-and-structure-discipline.md`
- `env-and-activation.md`
- `consult-knowledge-first.md`
- `producer-source-first.md`
- `<compute>.md` (若长跑 batch job)

---

## §3 Universal patterns (across all 4 archetypes)

### Pattern 1 — 4 件套契约（核心）

| 文件 | 角色 | 自述契约 |
|---|---|---|
| `blueprint.md` | WHY 层 / 长期 mission / 架构决策 | 顶部 "更新契机：架构级改动必 patch" |
| `CHANGELOG.md` | episodic memory / 决策-失败-经验 append-only | 顶部 "How to use this file" + "Entry format" |
| `Facts.md` 或 `facts/` | verified atomic claims | 顶部 "Trigger contract" / "格式约定" |
| `current-status.md` (仅 C 类) | 跨实验 live snapshot | 顶部 "区别于 result.md 和 CHANGELOG.md" |

### Pattern 2 — Rule auto-inject machinery

`<root>/.claude/rules/<name>.md` 顶部固定有：
```yaml
---
matcher:
  - "<path-glob>/**"
trigger_keywords: [<a>, <b>, ...]
---
```

**Rule §0 强制读 (mandatory at session start)**：
```bash
tail -n 100 <root>/CHANGELOG.md
cat <root>/blueprint.md
[cat <root>/Facts.md  if exists]
[cat <root>/current-status.md  if exists]
cat <root>/docs/repo-structure.md
```

**Rule §1 写流程**：决策性 commit 前 append CHANGELOG；架构改动 patch blueprint；Facts only 手动 trigger。

### Pattern 3 — Compute / cluster integration (optional)

如果项目涉及长跑 batch job：
- `<root>/activate.sh` —— 加载环境（conda / venv / module load / pyenv 等，按本地 env 写）
- `.claude/rules/<compute>.md`（如 `slurm.md` / `k8s.md` / `local-gpu.md`）—— partition / port / log path 硬规则
- `logs/` dir tracked
- **若 cluster 有 shared 只读盘**（如 SLURM 集群常见的 `/mnt/data/` / `/scratch/`）—— 规则里写"只读不写"
- **本通用版不预设 env activation / shared paths / partition name**。CoreWeave SLURM 具体配置见 `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/`。

### Pattern 4 — Knowledge base 选择性 symlink

如果项目需要 paper KB（archetype A/B 必，C/D 可选）：
- 真实目录 `KnowledgeBase/` (或 `knowledge-base/` / `knowledge/`)
- 内部 per-paper / per-topic 是 symlink → user 的 vault 或外部源
- `scripts/check_kb_sync.sh` + `scripts/refresh_kb.sh`（3 层 sync check：vault↔remote / symlinks↔topic md / no broken symlink）
- gitignore 屏蔽内容，whitelist scripts

### Pattern 5 — Gitignore boundary

每个 root 至少有：
- `0_debug/` 或等价 → gitignore'd
- KnowledgeBase / knowledge 内容 → gitignore'd (whitelist scripts)
- `<reference-gallery>/` 内容 → gitignore'd (whitelist README + .gitignore)
- Shared cluster paths (若 cluster) → 永远不入 git

### Pattern 6 — `.claude/settings.local.json` minimal

最小化 OMC state perms：
```json
{
  "permissions": {
    "allow": [
      "mcp__plugin_oh-my-claudecode_t__state_list_active",
      "mcp__plugin_oh-my-claudecode_t__state_clear"
    ]
  }
}
```

Archetype C 例外：`settings.json` 全套 hook + 大量 Bash allowlist。

---

## §4 Execution flow

### Phase 1 — Trigger deep-interview

```python
Skill("oh-my-claudecode:deep-interview")
# 注入 §1 的 8 个 mandatory dimension 作为 interview seed
```

Interview 收敛后 spec 落 `.omc/specs/pyu-harness-<project-slug>.md`。

### Phase 2 — 决定 scaffold 形态

根据 interview 答案：

| Answer to Q1 | Use template |
|---|---|
| Exploration | §2 Archetype A |
| Reproduction | §2 Archetype B |
| Active experimentation | §2 Archetype C |
| Dataset construction | §2 Archetype D |
| Mixed | A + 选项部分（user 决定） |

根据 Q2 决定 placement；根据 Q8 决定是否需要 cluster snippet 介入。

### Phase 3 — Stage-by-stage scaffold

按 6 个 stage 顺序执行：

1. **Stage 1** — Skeleton dirs + per-module `.gitignore`
2. **Stage 2** — `.claude/rules/` 4-7 rules
3. **Stage 3** — Core artifacts (blueprint / CHANGELOG / Facts / current-status)
4. **Stage 4** — `docs/` (repo-structure / workflow / harness)
5. **Stage 5** — KnowledgeBase (若有)
6. **Stage 6** — Verify acceptance (tree / sync check / git status / gitignore hits)

### Phase 4 — Hand-off

完成后：
1. 给 user 输出 4 件套相对路径 + 当前 KB sync status
2. 提示 "下次 `claude` 启动发'我回来了'，rule 会自动注入 4 件套到 context"
3. 给 commit suggestion（`feat(<scope>): bootstrap harness skeleton`）

---

## §5 Template fragments

### `blueprint.md` skeleton

```markdown
# <project> Blueprint

> 架构决策、参考 paper mapping、风险、开放问题。
> **更新契机**：架构级改动 / framework 级改动时必须 patch；阶段评审时更新。

## Table of Contents
- [Mission](#mission) - [Architecture](#architecture) - [Reference Papers](#reference-papers)
- [Success Criteria](#success-criteria) - [Risks](#risks) - [Open Questions](#open-questions)
- [Decisions](#decisions) - [Non-Goals](#non-goals)

---

## Mission
<一句话定义 + 阶段目标>

## Architecture
<高层架构图 / 数据流>

## Reference Papers
<KnowledgeBase 引用 + paper ↔ 项目组件 mapping>

## Success Criteria
- [ ] <可验证条件 1>
- [ ] <可验证条件 2>

## Risks
| Risk | 概率 | 影响 | 缓解 |
|---|---|---|---|
| <...> | 中 | 高 | <缓解策略> |

## Open Questions
1. **<问题>** — 何时决议、谁决议、依赖什么 evidence

## Decisions
> 已决议项；引 Open Question 编号 + commit / spec ref
- [YYYY-MM-DD] decision — <内容>（commit: pending）

## Non-Goals
- ❌ <显式排除范围>
```

### `CHANGELOG.md` skeleton

```markdown
# <project> CHANGELOG

> **Episodic memory** — 决策 / 失败 / 经验的"为什么"层。
> 不替代 `git log`（git log 记"做了什么"），此处记"为什么这么做 / 尝试失败的原因 / 下次应注意"。

## Table of Contents
- [How to use this file](#how-to-use-this-file)
- [Entry format](#entry-format)
- [\[unreleased\]](#unreleased)

---

## How to use this file
**强制流程**（由 `.claude/rules/<project>.md` 触发执行）：
1. **Session start** — `tail -n 100 CHANGELOG.md`
2. **决策性 commit 前** — append entry 到 `[unreleased]` 下对应分类
3. **PR 合并前** — `[unreleased]` → `[vYYYY-MM-DD-<slug>]`
4. **架构级改动** — 同时 patch `blueprint.md`

## Entry format
- [YYYY-MM-DD] <decision|failure|lesson|open-question> — <简述>（commit: <sha-short>）

---

## [unreleased]

### Decisions
_（空）_

### Failures
_（空）_

### Lessons
_（空）_

### Open Questions
_（空）_
```

### Main rule `<project>.md` skeleton

```markdown
---
matcher:
  - "<scope-glob>/**"
trigger_keywords: [<project>, <key terms>]
---

# <project> Module Rule

## §0 强制读写流程

### Session start —— 读
\`\`\`bash
tail -n 100 <root>/CHANGELOG.md
cat <root>/blueprint.md
[cat <root>/Facts.md or current-status.md]
cat <root>/docs/repo-structure.md
\`\`\`

### Session 结束 —— 写
决策性 commit 前必须 append entry 到 `CHANGELOG.md [unreleased]`。

### 架构级改动 —— patch blueprint
<列出哪些算架构级>

## §2 <项目特定 scope 边界>
## §3 命名约定
## §4 Compute / batch job 引用 (若有)
详见 `.claude/rules/<compute>.md`
## §5 PR 拆分建议
## §6 Facts 写入契约（若 single-file Facts）
仅 user 手动 trigger；每 entry 必须带溯源（commit hash / exp_id / journal path）。
```

### SessionStart hook（archetype C 必备）

`<root>/.claude/hooks/session_start_inject.sh`：
```bash
#!/bin/bash
echo "=== <project> session start ==="
echo "--- CHANGELOG tail ---"
tail -n 50 "$CLAUDE_PROJECT_DIR/CHANGELOG.md"
echo "--- current-status.md ---"
cat "$CLAUDE_PROJECT_DIR/current-status.md"
echo "--- blueprint TOC ---"
awk '/^## Table of Contents/,/^---/' "$CLAUDE_PROJECT_DIR/blueprint.md"
```

`<root>/.claude/settings.json`：
```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/session_start_inject.sh"
      }]
    }]
  }
}
```

---

## §6 Anti-patterns

- ❌ **跳过 deep-interview**：8 个 dimension 任一不清 → 后续 scaffold 必有 drift
- ❌ **强行 archetype A 模板**：每个项目都套 exploration scaffold（应按 deep-interview 答案选）
- ❌ **不查 env**：忽视 conda/venv env、partition、shared paths、batch job 约定
- ❌ **写 placeholder Mission**：blueprint Mission 必须用 user interview 原话或精确提炼，不写"TBD"
- ❌ **写 empty TOC 不写 body**：每个 ## section 至少 skeleton + 一句话指引
- ❌ **不验证 acceptance**：Stage 6 漏跑 → gitignore / sync check 可能从一开始就坏
- ❌ **不给 commit suggestion**：完成后必须明确告诉 user 下一步 commit message
- ❌ **改 user 的外部 vault**：vault 是 user 私有 source，skill 只 symlink，不写内容
- ❌ **过度优化**：不给 archetype A 项目加 SessionStart hook（A 没那么需要）

---

## §7 Maintenance & evolution

本 skill 随经验更新：
- 每次 setup 完成后，user 反馈痛点 → 加进 §6 anti-patterns
- 出现新 archetype → 加进 §2
- 出现新 universal pattern → 加进 §3
- Templates 改进 → 更新 §5

Skill 本身的 CHANGELOG 写在 `~/.claude/skills/pyu-harness-setup-generic/CHANGELOG.md`（可选）。

---

## §8 Quick command

```
/skill pyu-harness-setup-generic [--at <target_dir>] [一句话项目描述]
```

或在自然对话中说"setup harness" / "起 harness" / "新项目 harness" 等关键词 → skill 自动 fire。

Skill 入口立即 spawn deep-interview 子 skill —— 不允许直接动手 scaffold。
