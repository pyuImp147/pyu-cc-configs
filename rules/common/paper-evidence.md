# Paper Evidence Rule (Cross-Project)

> 适用范围：所有项目。任何涉及"论文原文内容"的问题必须走 evidence-first 流程。
> 注入时机：User 的 question 含以下关键词之一 → 强制触发本规则：
> - 论文、paper、原文、Paper 名称（e.g. "D4RT", "VGGT", "CoTracker3"）
> - architecture、encoder、decoder、layer count、head 数量、hidden dim、parameter count
> - 训练细节（lr / batch / epochs / loss / schedule / augmentation / dataset split）
> - eval / benchmark 数字（APD3D / OA / 3D-AJ / PSNR / SSIM / etc.）
> - 实验设置、ablation、超参、方法细节、consistency claim

## 核心原则

**不基于当前 context（memory / conversation / 之前的回答）回答论文事实**。每次都**重读原文**并给出**具体证据引用**（page / section / figure / table / 行号）。

## 为什么

- AI 的 context 会压缩 / 漂移 / 被旧 session 污染
- Paper 信息高价值、易错、user 用这些做 research decision
- "大致记得" ≠ "原文写什么"；一次错误引用可能浪费数天 experiment 时间
- 可追溯（reproducible）是 research 基本要求

## 强制流程

遇到 paper-related 问题时**必须**执行：

### 1. 定位原文文件

| 项目格式 | paper 原文位置惯例 |
|---|---|
| Per-paper md 格式 | `docs/papers/<PaperName>/paper-raw.md` (一手转录) + `<PaperName>.md` (二手笔记) |
| Legacy pdf+txt 格式 | `docs/papers_raw/*.{pdf,txt}` 或 `papers/*.{pdf,txt}` |
| 未约定 | `find . -name "*.pdf" -path "*paper*"` 或询问 user |

**Per-paper md 格式特别约定**（如果项目采用此 layout）：
- 每个 paper 目录 `docs/papers/<PaperName>/` 下有两个核心 md：
  - `<PaperName>.md` —— 笔记 / 重点（user 个人整理，二手）
  - `paper-raw.md` —— **原文转录**（evidence 来源，一手）
- **paper 问题一律读 `paper-raw.md`**（不读 `<PaperName>.md` —— 那是二手）

Legacy pdf+txt 格式时：优先读 `.txt`（快速 grep）；需要看图表 / 公式时读 `.pdf`。

> 当前 cluster 上具体哪些项目走哪种 layout（如 `imp_genai-d4rt-v1` / `TrackingModel_Gallery`），见 `optional/cluster-snippets/paper-evidence-projects.md`。

### 2. 读取证据

```bash
# 快速匹配（txt 版）
grep -n -i -A 3 -B 1 "<keyword>" <paper>.txt

# 或 Read tool 精准翻页
Read(<paper>.pdf, pages="3-5")
```

**必须**读到具体 section / table / figure 的原文，不引用 abstract-level 泛述。

### 3. 回答格式

```markdown
**[原文结论]**
<直接引用或精确概括>

**Evidence**:
- 文件：`<path>.pdf` page <N> / `<path>.txt` L<M>-L<K>
- 原文片段：> "..."
- Section：<§X.Y / Table N / Figure N>
```

若原文**没有明确记载**该信息：

```markdown
**Not explicitly stated in paper.**
- 最接近的证据：<path> page <N>: "..."
- 可能的 inference：<你的推断>（标注"推断"，不混淆 fact）
```

### 4. 多 paper 对比

对比性问题（"A vs B 的 encoder 层数"）→ **分别**读两篇 paper，**分别**给证据。禁止"根据之前对比记忆"。

## 禁止模式

- ❌ "记得 D4RT 用了 24 层 encoder"（未读原文）
- ❌ "根据之前的对比文档..."（二手资料，可能本身就错）
- ❌ "一般来说这类模型..."（一般化推测代替原文）
- ❌ 只读 abstract 就回答 detail 问题
- ❌ 只读 conclusion 就回答 method 问题

## 允许的例外

- 用户明确说"不用查，直接按你的记忆讲"
- 问题是**通用常识**（"transformer 什么是 attention" 这种）
- 已在**本轮对话同一文件**读过并给过引用（可在该轮对话内复用）
- 架构 high-level 类比（"D4RT 类似 VGGT 的思路"）—— 但若追问数字必须重读

## 本规则 + 项目 wiki 的分层

**Paper-per-folder md 格式**（推荐 layout）：
- `docs/papers/<PaperName>/paper-raw.md` — **一手原文**（evidence 来源）
- `docs/papers/<PaperName>/<PaperName>.md` — 二手笔记（user 个人整理）
- `docs/papers/topics/topic - <name>.md` — topic 索引（跨 paper 主题聚合）

**Legacy pdf+txt 格式**：
- `docs/papers/by-paper/<name>.md` — 项目维护的 wiki，**二手整理**
- `docs/papers/papers_raw/<name>.{pdf,txt}` — **一手原文**（evidence 来源）

**规则**：
1. 用户问问题 → 读**原文**（`paper-raw.md` 或 `papers_raw/`）
2. 原文给不出 → 看二手笔记作为补充 context，但必须**标注**"二手内容，非原文"
3. 发现二手与原文冲突 → 修二手 + 在 CHANGELOG 记录

> 项目特定的 layout 实证（当前 cluster 上的 `imp_genai-d4rt-v1` 等）见 `optional/cluster-snippets/paper-evidence-projects.md`。

## Quick checklist（回答前自查）

- [ ] 我是否**真的**打开了 paper 文件？
- [ ] 我是否给了具体 page / line / section？
- [ ] 我是否引用了**原文片段**（不是自己的概括）？
- [ ] 若是对比，两篇都读了吗？
- [ ] 原文不记载时，是否明确标注"not explicitly stated"？
