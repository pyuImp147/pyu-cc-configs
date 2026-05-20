---
name: pyu-harness-setup
description: Bootstrap a self-enforcing harness system (blueprint + CHANGELOG + Facts/current-status + KB + rules) for a new research project on the CoreWeave cluster. Adapts to 4 project archetypes (exploration / reproduction / experimentation / dataset). MANDATORY first step — trigger /oh-my-claudecode:deep-interview to clarify project goal, scope, and project-type before scaffolding.
argument-hint: "[--at <target_dir>] [project description]"
trigger_keywords: [pyu-harness-setup, new project harness, harness setup, setup harness for, 起 harness, 新项目 harness]
---

# pyu-harness-setup — Project Harness Bootstrap

> **Use when**: 一个**新**项目 / **新**模块 / **新**worktree 需要 setup 一套"自动维护 long-run context + 知道 current status + 历史追踪 + cluster-ready"的 harness 系统。
> **Do NOT use when**: 项目已有 `blueprint.md` + `CHANGELOG.md` + `.claude/rules/`（已有 harness，直接用）。
> **Pattern source**: 提炼自 user 4 个项目 — `imp_genai-d4rt-v1`（reproduction）/ `imp_genai-chaowei-tracking-GS`（exploration + integration）/ `selfEvo`（active experimentation）/ `data-explore`（dataset construction）。

---

## §0 What this skill produces (vs what it isn't)

### NOT 散件文件

**单独** `blueprint.md` 没用；**单独** rule 没用。本 skill 产出的是 **5 个机制互锁的闭环**：

1. **Self-injecting** — Rule auto-fire（matcher / trigger_keywords / SessionStart hook）
2. **Self-naming** — Rule §0 列出 mandatory tail/cat 路径；这些路径都被 skill 创建
3. **Self-explaining** — 每个 artifact 顶部自述契约（"How to use this file"）
4. **Self-checking** — KB sync script + gitignore boundary 主动屏蔽错误状态
5. **Self-recording** — CHANGELOG append-only + Facts/current-status 验证状态

详见之前 audit 输出：rule 注入 → 强制 tail 4 件套 → 决策性 commit 提醒 append → 架构改动强制 patch blueprint → KB 操作强制 sync check。

### Cluster-adapted

集群环境固定 = CoreWeave H100 / RTX Pro 6000，`source activate.sh` 入口，`/mnt/data/` 共享盘，`/mnt/home/pengcheng.yu/` 个人盘，conda env `imp_genai`。所有 sbatch / 路径约定都按此适配。

---

## §1 MANDATORY: Trigger /deep-interview first

接到本 skill invoke，**第一步**调 `Skill("oh-my-claudecode:deep-interview")` 把以下 8 个核心 ambiguity 问清楚。**不允许跳过**：用户给的 1 句话描述对 harness 设计远远不够。

### 8 个 mandatory clarification 问题

deep-interview 至少要走通这 8 个 dimension（顺序按"最高 leverage 先问"）：

1. **Project archetype** ★ 决定整套 scaffold 形态
   - (a) **Exploration**：survey SOTA / 跑别人 method / 决定方向（如 `tracking-GS` 早期、`data-explore`）
   - (b) **Reproduction**：复现一篇 paper / 一套 baseline（如 `d4rt-v1`）
   - (c) **Active experimentation**：已有 model，跑大量 ablation（如 `selfEvo`）
   - (d) **Dataset construction**：从 raw data 构造 / 验证 dataset（如 `data-explore`）
   - (e) **Mixed**：(a) + (c) 等组合（如 `tracking-GS` 后期）

2. **Module placement** — 项目是
   - (i) **Standalone repo** at `~/code/<project>/`（如 selfEvo, data-explore）
   - (ii) **Worktree of monorepo** at `~/code/<monorepo>-<branch>/`（如 d4rt-v1, tracking-GS — `imp_genai` worktree）
   - (iii) **Module within an existing worktree** at `<worktree>/research/<area>/<module>/`

3. **Long-term goal** — 一句话定义"项目跑完算成功"是什么？必须可写进 blueprint Mission。

4. **Time horizon** — 几周 / 几月 / 长期？决定 `current-status.md` 是否需要。
   - < 2 周 → 不需要 current-status，CHANGELOG `[unreleased]` 够
   - 2 周–3 月 → 需要 current-status.md（live snapshot）
   - > 3 月 + 多 ablation 集中 → 需要 SessionStart hook 自动注入 current-status

5. **Knowledge base scope** — 是否需要 paper KB？
   - 不需要 → 跳过 KnowledgeBase
   - 需要 → 哪些 obsidian-vault topics 在 scope？（user 在 vault 维护 `topics/topic - <name>.md` index）

6. **External reference repos** — 是否要 `tracking-gallery/` 风格的只读 clone 区？
   - exploration / reproduction 通常需要
   - active experimentation 通常**不**需要

7. **Verified facts 存储** — single-file 还是 dir？
   - 项目验证过的 fact 少且杂 → `Facts.md` (single file，类似 tracking-GS)
   - 项目按主题积累很多 atomic claim → `facts/<topic>.md` dir (类似 data-explore)

8. **Cluster integration intensity** — 是否长跑 sbatch？是否需要 wandb / tensorboard log 在 `logs/`？

deep-interview 收敛到 ambiguity ≤ 20% 后才允许进 scaffold。

---

## §2 Architecture: 4 archetypes ↔ 模板差异

每个 archetype 对应**一组**变体。Skill 根据 deep-interview 答案选模板。

### Archetype A — Exploration

**例子**：tracking-GS 早期、data-explore 早期、新方向 survey
**特征**：未知数大，先看别人怎么做，后决定路径

**Scaffold**：
```
<root>/
├── blueprint.md          ← Mission + Open Questions 重 / Decisions 轻
├── CHANGELOG.md          ← Decisions / Failures / Lessons / Open Questions
├── Facts.md              ← single file（早期 fact 少）
├── docs/
│   ├── repo-structure.md ← where-does-it-go
│   ├── workflow.md
│   └── harness.md
├── KnowledgeBase/        ← obsidian-vault 选择性 symlink
│   ├── topics/<4-6 topic>.md
│   ├── <PaperName>/      ← per-paper symlink
│   └── scripts/{check_kb_sync.sh, refresh_kb.sh}
├── tracking-gallery/     ← ★ 只读参考 clone 区（archetype A 必备）
│   ├── .gitignore (* + !README.md)
│   └── README.md (clone list)
├── scripts/              ← 主代码
├── viewer/               ← 可视化
└── 0_debug/              ← 临时输出（.gitignore'd）
```

**Rules**: `<project>.md` (主) + `knowledge-base.md` + `slurm.md` + `github-workflow.md` (若 imp_genai worktree)

### Archetype B — Reproduction

**例子**：d4rt-v1
**特征**：明确 paper，明确 SOTA target，分阶段验证

**Scaffold**：
```
<root>/
├── blueprint.md              ← Decisions 重，Architecture 明确，sub-blueprint 可拆
├── CHANGELOG.md
├── docs/
│   ├── papers/<PaperName>/   ← 主要参考 paper KB（per-paper folder）
│   ├── model-arch/           ← 每个模型组件 deep-dive
│   ├── data/                 ← 数据格式 deep-dive
│   ├── training/             ← 训练机制 deep-dive
│   ├── archive/              ← 弃用文档（不删，留 context）
│   ├── repo-structure.md
│   ├── workflow.md
│   └── harness.md
├── experiments/              ← per-run journal（current-agreements.md + <exp_id>/）
├── model/blueprint.md        ← 子模块级 sub-blueprint
├── external/                 ← 只读 reference repos
├── d4rt_community_versions/  ← 社区复现对比
└── scripts/ / configs/ / lightning/ / losses/ / metrics/ ...
```

**Rules**: `<module>.md` (主) + `knowledge-base.md` + `evaluation-<topic>.md`（评估专用）+ `slurm.md` + `github-workflow.md`

### Archetype C — Active Experimentation

**例子**：selfEvo
**特征**：已有 model，多 ablation 同时跑，需要 cross-experiment snapshot

**Scaffold**：
```
<root>/
├── blueprint.md
├── CHANGELOG.md
├── current-status.md         ← ★ 跨实验 live snapshot（archetype C 必备）
├── docs/
├── experiments/              ← 多 ablation 子目录，per-run result.md
│   ├── ablation-v1/
│   ├── ablation-v2/
│   ├── aggregate_eval.py
│   ├── experiment.md
│   └── _summary_plots.py
├── knowledge-base/           ← 项目内 KB（不一定从 vault symlink）
├── src/                      ← 主 model 代码
├── slurm/                    ← per-experiment sbatch templates
├── eval/ / eval-set/         ← 评估代码 + 评估数据
├── logs/
└── reference/                ← 别人代码（如果有）
```

**Rules**: `<project>.md` (主，明示 SessionStart hook inject current-status)
**Hooks**: `.claude/hooks/session_start_inject.sh` 必备 — auto-tail CHANGELOG + auto-cat current-status

### Archetype D — Dataset Construction

**例子**：data-explore
**特征**：从 raw data 构造数据集，多 atomic verified fact

**Scaffold**：
```
<root>/
├── blueprint.md
├── CHANGELOG.md
├── docs/
│   ├── structure.md          ← live folder map（同 repo-structure.md）
│   └── deferred/             ← known-but-not-yet-done
├── facts/                    ← ★ 主题分 file（archetype D）
│   ├── <topic-1>.md
│   ├── <topic-2>.md
│   └── README.md
├── knowledge/                ← 内嵌 paper / topic
│   ├── <topic>/
│   └── topics/
├── 0_debug/                  ← 中间产物、smoke test 输出
├── scripts/                  ← 主代码（query / verify / preprocess）
│   ├── tmp-debug/            ← 临时探索
│   └── <main>.sbatch
├── refer_datasets/           ← 外部 dataset 引用（.gitignore data）
└── <data-source>/            ← 项目主要数据源 dir（如 metaHuman/）
```

**Rules**: 7 个细粒度 rule（data-explore 实测 effective）：
- `session-start-mandatory-read.md` (matcher `**`)
- `0-debug-output.md` (中间产物去哪)
- `changelog-and-structure-discipline.md`
- `conda-env-and-activation.md`
- `consult-knowledge-first.md`
- `producer-source-first.md`
- `sbatch-for-heavy-tasks.md`

---

## §3 Universal patterns (across all 4 archetypes)

### Pattern 1 — 4 件套契约（核心）

**ALL archetypes 都有**至少这 3 个（C 类多 1 个）：

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
cat <root>/docs/repo-structure.md (或 docs/structure.md)
```

**Rule §1 写流程**：决策性 commit 前 append CHANGELOG；架构改动 patch blueprint；Facts only 手动 trigger。

### Pattern 3 — Cluster integration

`<root>/activate.sh`（standalone）或 `imp_genai/activate.sh`（worktree）—— 加载 conda env + HF_HOME + PYTHONPATH。
`.claude/rules/slurm.md`（或 `sbatch-for-heavy-tasks.md`）—— partition / MASTER_PORT / log 路径硬规则。
`logs/` dir tracked，`/mnt/data/` 只读不写。

### Pattern 4 — Knowledge base 选择性 symlink

如果项目需要 paper KB（archetype A/B 必，C/D 可选）：
- 真实目录 `KnowledgeBase/` (或 `knowledge-base/` / `knowledge/`)
- 内部 per-paper / per-topic 是 symlink → `~/obsidian-vault/Papers-Claude/`
- `scripts/check_kb_sync.sh` + `scripts/refresh_kb.sh`（3 层 sync check: vault↔remote / symlinks↔topic md / no broken symlink）
- gitignore 屏蔽内容，whitelist scripts

### Pattern 5 — Gitignore boundary

每个 root 至少有：
- `0_debug/` 或等价 → gitignore'd
- KnowledgeBase / knowledge 内容 → gitignore'd (whitelist scripts)
- `tracking-gallery/` / `external/` 内容 → gitignore'd (whitelist README + .gitignore)
- `/mnt/data/` 永远不入 git

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

Archetype C (selfEvo) 例外：`settings.json` 全套 hook + 大量 Bash allowlist（活跃实验需要少 permission prompt）。

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

根据 Q2 决定 placement：
- Standalone → 直接在 `~/code/<project>/` 起
- Worktree → `git worktree add` 已完成的前提下，在 worktree 根 + 对应 module subdir
- Module in worktree → 模块子目录起 artifacts，`.claude/` 在 worktree 根

### Phase 3 — Stage-by-stage scaffold

按 6 个 stage 顺序执行（参考 `tracking-GS/.omc/specs/deep-interview-tracking-GS-harness-setup.md`）：

1. **Stage 1 — Skeleton dirs + per-module .gitignore**
   - mkdir 所有目录
   - 写 `.gitignore` for `0_debug/` + `KnowledgeBase/*` + `tracking-gallery/*`

2. **Stage 2 — `.claude/rules/` 4-7 rules**
   - 主 rule `<project>.md` (新写)
   - `knowledge-base.md` (若 KB)
   - `slurm.md` (cluster generic)
   - `github-workflow.md` (若 imp_genai worktree)
   - Archetype D 加细粒度 5 个 rule
   - `.claude/settings.local.json`

3. **Stage 3 — Core artifacts**
   - `blueprint.md`（按 archetype template）
   - `CHANGELOG.md`（统一 schema）
   - `Facts.md` 或 `facts/README.md`（按 Q7）
   - `current-status.md`（仅 C 类）

4. **Stage 4 — `docs/`**
   - `repo-structure.md`（统一 schema：tree + decision table + filename conventions + anti-patterns）
   - `workflow.md`（session start / 5 task workflows / session end checklist）
   - `harness.md`（三层结构 + rule 表 + cherry-pick map）

5. **Stage 5 — KnowledgeBase（若有）**
   - mkdir 真实目录
   - 写 `scripts/check_kb_sync.sh` + `refresh_kb.sh`（fork 自 d4rt-v1 模板，改 topic list + 路径）
   - 跑一次 refresh 拉 obsidian-vault symlinks

6. **Stage 6 — Verify acceptance**
   - tree 检查所有 path
   - `bash check_kb_sync.sh` 必 exit 0
   - `git status` 不显示 0_debug / KB content / gallery content
   - `git check-ignore -v` 验证 gitignore 命中

### Phase 4 — Hand-off

完成后：
1. 给 user 输出 4 件套相对路径 + 当前 KB sync status
2. 提示 "下次 `claude` 启动发'我回来了'，rule 会自动注入 4 件套到 context"
3. 给 commit suggestion（`feat(<scope>): bootstrap harness skeleton`）

---

## §5 Template fragments

### `blueprint.md` skeleton（archetype-agnostic 骨架）

```markdown
# <project> Blueprint

> 架构决策、参考 paper mapping、风险、开放问题。
> **更新契机**：架构级改动 / framework 级改动时必须 patch；阶段评审时更新。
> PR review 会检查 blueprint 是否与代码同步。

## Table of Contents

- [Mission](#mission)
- [Architecture](#architecture)
- [Reference Papers](#reference-papers)
- [Success Criteria](#success-criteria)
- [Risks](#risks)
- [Open Questions](#open-questions)
- [Decisions](#decisions)
- [Non-Goals](#non-goals)

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

```markdown
- [YYYY-MM-DD] <decision|failure|lesson|open-question> — <简述>（commit: <sha-short>）
  <可选：1-3 行补充>
```

---

## [unreleased]

### Decisions
_（空 — 由 session 写入）_

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

## §0 强制读写流程（最重要）

### Session start —— 读

```bash
tail -n 100 <root>/CHANGELOG.md
cat <root>/blueprint.md
[cat <root>/Facts.md or current-status.md]
cat <root>/docs/repo-structure.md
```

### Session 结束 —— 写

决策性 commit 前必须 append entry 到 `CHANGELOG.md [unreleased]`。

### 架构级改动 —— patch blueprint

<列出哪些算架构级>

## §1 imp_genai 12 条硬约束（若 imp_genai worktree）

<复制 / 引用>

## §2 <项目特定 scope 边界>

## §3 命名约定

## §4 SLURM 引用

详见 `.claude/rules/slurm.md`

## §5 PR 拆分建议

## §6 Facts 写入契约（若 single-file Facts）

仅 user 手动 trigger；每 entry 必须带溯源（commit hash / exp_id / journal path）。
```

### SessionStart hook（archetype C 必备）

`<root>/.claude/hooks/session_start_inject.sh`：
```bash
#!/bin/bash
echo "=== <project> session start ==="
echo ""
echo "--- CHANGELOG tail ---"
tail -n 50 "$CLAUDE_PROJECT_DIR/CHANGELOG.md"
echo ""
echo "--- current-status.md ---"
cat "$CLAUDE_PROJECT_DIR/current-status.md"
echo ""
echo "--- blueprint TOC ---"
awk '/^## Table of Contents/,/^---/' "$CLAUDE_PROJECT_DIR/blueprint.md"
```

`<root>/.claude/settings.json`：
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/session_start_inject.sh"
          }
        ]
      }
    ]
  }
}
```

---

## §6 Pattern reference (与已有项目对照)

| 项目 | Archetype | KB | Facts 格式 | Reference repos | current-status | SessionStart hook |
|---|---|---|---|---|---|---|
| `imp_genai-d4rt-v1` | B (Reproduction) | `docs/papers/` (in-module) | 无（用 CHANGELOG Lessons） | `external/` + `d4rt_community_versions/` | 无 | 无 |
| `imp_genai-chaowei-tracking-GS` | A + B (Exploration + Integration) | `KnowledgeBase/` (module root) | `Facts.md` (single file) | `tracking-gallery/` | 无 | 无 |
| `selfEvo` | C (Active Experimentation) | `knowledge-base/` | 无 | 无 | ✅ `current-status.md` | ✅ |
| `data-explore` | D (Dataset Construction) | `knowledge/` | `facts/<topic>.md` (multi-file) | 无（refer_datasets/ 是数据） | 无 | 无 |

Skill 会在 Phase 2 推荐其中一个为 closest match，并 cite 其 path 让 user 阅读为 reference。

---

## §7 Anti-patterns（skill 不该做的）

- ❌ **跳过 deep-interview**：8 个 dimension 任一不清 → 后续 scaffold 必有 drift
- ❌ **强行 archetype A 模板**：每个项目都套 exploration scaffold（应按 deep-interview 答案选）
- ❌ **不查 cluster env**：忽视 conda env、partition、`/mnt/data/` 共享盘约定
- ❌ **写 placeholder Mission**：blueprint Mission 必须用 user interview 原话或精确提炼，不写"TBD"
- ❌ **写 empty TOC 不写 body**：每个 ## section 至少 skeleton + 一句话指引
- ❌ **不验证 acceptance**：Stage 6 漏跑 → gitignore / sync check 可能从一开始就坏
- ❌ **不把 commit suggestion 给 user**：完成后必须明确告诉 user "下一步 commit `feat(<scope>): bootstrap harness skeleton`"
- ❌ **改 user 的 vault**：vault 是 user obsidian clone，skill 只 symlink，不写内容
- ❌ **过度优化**：不给 archetype A 项目加 SessionStart hook（A 没那么需要，反而增加复杂度）

---

## §8 Maintenance & evolution

本 skill 随经验更新：
- 每次 setup 完成后，user 反馈痛点 → 加进 §7 anti-patterns
- 出现新 archetype → 加进 §2
- 出现新 universal pattern → 加进 §3
- Templates 改进 → 更新 §5

Skill 本身的 CHANGELOG 写在 `~/.claude/skills/pyu-harness-setup/CHANGELOG.md`（可选）。

---

## §9 Quick command

User 触发：

```
/skill pyu-harness-setup [--at <target_dir>] [一句话项目描述]
```

或在自然对话中说"setup harness" / "起 harness" / "新项目 harness" 等关键词 → skill 自动 fire。

Skill 入口立即 spawn deep-interview 子 skill —— 不允许直接动手 scaffold。
