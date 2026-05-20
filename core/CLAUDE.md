<!-- User customizations (portable) -->
# Global Instructions

## Identity
PhD researcher in AI — 3D/4D computer vision, generative models, and agents.
Primary framework: PyTorch.
Daily workflow: processing 3D/4D/image/video datasets and dataloading, understanding and converting camera conventions (OpenCV, OpenGL, Blender, PyTorch3D, Unreal, etc.), data visualization (depth/masks/confidence maps, 3D geometry), reading/understanding model architectures, training and tuning modern transformer-based models, distributed training, and MLSys optimization, run experiments with different args.

> Cluster / SLURM / conda specifics live in `optional/cluster-snippets/cluster-env.md`. Append that snippet to this file when running on the CoreWeave-style SLURM cluster; skip on mac / non-cluster hosts.

## Tooling
- **IDE**: VSCode (local on mac; remote SSH on cluster)
- **3D Visualization**: viser (https://viser.studio) — primary tool for visualizing pointmaps, 3D Gaussians, cameras, meshes in a single viewer
- **2D Visualization**: matplotlib, OpenCV for masks, depth maps, confidence maps, etc.
- **Model/Data Hub**: HuggingFace — frequently download datasets and model checkpoints (use `HF_HOME` for cache location; cluster has a shared cache, see cluster snippet)

## Language
- 日常交流用中文，technical terms 保持英文
- Code comments 和 docstrings 用英文
- Git commit messages 用英文

## Philosophy
I am a researcher, not a product engineer. Prioritize:
- **Idea/functionality first** — get it working, then clean up if needed
- **Simple, direct, readable code** — easy to debug, easy to modify
- **No over-engineering** — no complex abstractions, no premature optimization, no production-grade patterns (fancy GUIs, elaborate error hierarchies, plugin systems, etc.)
- **Minimal boilerplate** — if 10 lines of straightforward code works, don't wrap it in 3 classes
- **Research velocity** — fast iteration > perfect architecture

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.

## Explanation Guideline:
When I ask you to explain a concept or answer a question, please adopt a Top-Down Approach and follow these rules:
1. Core Rule (Always Apply): > Always start with a high-level overview and, if applicable, a geometric or conceptual intuition. Help me grasp the "big picture" before diving into anything else.
2. Conditional Depth (Adapt to Query Type):
IF I ask for technical details: Provide low-level explanations, mathematical equations, and pseudocode if applicable.
IF I ask about specific implementations/mechanisms (e.g., how a specific paper models a concept): Include one or more concrete examples (with actual numbers/shapes, code or numerical illustrations) to illustrate the point.
IF I ask for a code explaination: provide low-level explanations with corresponding code (how concepts and code are connected and related), help me with the data flow and show clear tensor shape.
IF I ask for a summary, overview, or simple comparison: Keep the response high-level and concise. Do NOT include low-level technical details, math, or specific examples unless I explicitly request them.

## Paper Questions (Evidence-First)

**ANY question about paper content** — architecture details, layer counts, training hyperparams, benchmark numbers, ablation results, method specifics — MUST follow evidence-first protocol:

1. **Do NOT answer from context / memory / prior conversation** — always re-read the original paper.
2. **Locate the raw paper** (project-specific locations):
   - `imp_genai-d4rt-v1`: `research/scene4d/feed_forward_tracker/docs/papers/<PaperName>/paper-raw.md` (一手原文转录). 二手笔记在同目录的 `<PaperName>.md`. ⚠ **`docs/` 被 `.gitignore` 屏蔽** → Glob / Grep 工具看不见，必须用 `Read` 精确路径或 `Bash ls` / `Bash grep` 绕开。
   - `TrackingModel_Gallery`: `docs/papers_raw/*.{pdf,txt}`
   - Other projects: grep for `*.pdf` under `docs/`/`papers/` or ask user.
3. **Read specific evidence** — for `.md` paper-raw: grep keywords with `Bash grep` (Grep tool 受 gitignore 影响), Read sections directly. For legacy `.pdf` / `.txt`: Read `.pdf` with pages=, grep `.txt`.
4. **Answer with evidence block**:
   ```
   [Answer]
   Evidence:
   - File: <path>.pdf page <N> / <path>.txt L<M>-L<K>
   - Quote: > "..."
   - Section: <§X.Y / Table N / Figure N>
   ```
5. If not explicitly stated in paper → say so, don't guess.

Full rule: `~/.claude/rules/common/paper-evidence.md`

## Documentation

**Distinguish two doc types** — they need different styles. Don't confuse one for the other.

### Type 1: Code reference docs (`docs/`, project-internal)
Dense reference for "what does this code do, with what shapes, called from where". Reader is the user themselves coming back after weeks. Goal = build mental model in 10 min, then jump to code.

**Required**: 1-2 句 intro → TOC → 模块 / file→class 表 → Pipeline Mermaid（canonical 数值如 `B=2,S=8,H=W=518`，每条边标 tensor shape）→ deep-dive 章节（每节配 ≤15 行 code quote + 简短解释）→ config 映射表 → 已知 paper-vs-code 不一致（编号 D1..Dn）。

**Forbidden**:
- ❌ TL;DR / 一句话做法 / Mental model / metaphor
- ❌ "作者在卖什么" / "哪个组件最关键"
- ❌ Limitations / Open questions / TODO 这类 paper-digest 装饰
- ❌ 关键数字凑数表
- ❌ 引言式废话 ("在本文档中我们将探讨...")
- ❌ emoji
- ❌ 任何"文学化"段落

**长度**：400-700 行 / doc。Density > length。可以表格的不要散文，可以 bullet 不要长句。

**语言**：中文为主，technical term / class name / file path / function / shape / 数值用英文。每段叙述应该通过 "is this English?" 检查 —— 不要写英文 narrative 段落。

### Type 2: Paper digest / blog-style notes (`knowledge-base/<paper>/`)
读论文后整理的笔记。**Academic + Blog style** —— deeply analytical and properly cited, highly readable, engaging narrative。可以用 TL;DR / Mental model / metaphor / "作者在卖什么" / "哪个组件最关键" / Limitations / Open questions —— 这些都是 paper digest 合法装备。但不要把这套装备搬到 Type 1 doc。

### 通用要求（两类都适用）
- Data flow / pipeline 必须 Mermaid 图，每条边标 tensor shape
- Architecture: high-level overview + per-module breakdown
- Code refs：`path/file.py:Lline` 格式，line-precise，方便 jump-to
- Save to `docs/` (Type 1) or `knowledge-base/` (Type 2)

### Lessons learned (selfEvo doc rewrite cycles)
- **不要把 paper digest 的章节模板搬到 code reference doc**。看到 `knowledge-base/<paper>.md` 不代表那是项目通用 style。
- **Doc 写作走 sonnet**（per `<model_routing>`），不要无脑 opus —— 慢 3-5x 没必要。
- **Density 比长度重要**。450 行聚焦的胜过 1100 行啰嗦的。
- **Diagram 用 canonical numerical example**（`B=2, S=8` 等），不要抽象 `B/S/H/W`。
- **小修改不要 spawn agent**。<200 行 edit 直接主对话做。
- **已有配置先 follow，不要加新层**。User 已有 `<model_routing>` / rules / hooks，先看再用，不要"补一个新机制"。

## Safety
- Always confirm before `rm` on data directories
- When modifying training configs, show diff before applying
- For shared / cluster storage rules (e.g. `/mnt/data/` safety on CoreWeave), see `optional/cluster-snippets/cluster-env.md`.

## Tool usage gotchas (HARD RULES)

### Edit / Write require a session-local Read on the EXACT path

`Edit` 和 `Write` 工具在 session 内对一个文件做修改前，**必须先 Read 一次该文件的当前路径**。否则会报 `File has not been read yet` 错。

- 「我之前在别处看过这个文件 / 在 grep / Bash output / system-reminder / 旧 session 里读过内容」**不算**已读
- 「我刚刚 mv 了这个文件到新路径」之后，要 Edit / Write 新路径需要重新 Read 新路径（即使内容跟旧路径一样）
- 「这个文件是我刚刚 Write 创建的」之后再 Edit 它通常没问题（harness 把 Write 也算一次）。但 mv 之后的新路径**必须**重新 Read

**操作模式：批量修改前先并行 Read 所有目标文件**，再做 Edit。不要边 mv 边 Edit。不要靠"间接知道内容"省 Read。

每次掉进这个坑（包括 mv 后 Edit、grep 后 Edit、跨 session 后 Edit），用户都要花一句话提醒。代价：用户挫败 + 多消耗 1 个 tool call。

预防：把"现在要 Edit / Write 哪些文件"列出来后，第一步就是并行 Read 所有路径。即使是 mv 自己刚刚做的目标路径也要 Read。
