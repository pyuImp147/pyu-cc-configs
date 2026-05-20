# Paper Evidence — Project-Specific Lookup (current cluster)

> Appendix to `rules/common/paper-evidence.md`. **仅当**目标 host 上确实有这些 project worktree 时启用。
> 这些项目名（如 `imp_genai-d4rt-v1`）含 conda env 名 `imp_genai`，是 cluster-coupled，因此放在 cluster snippet。

## 项目 → paper 原文路径

| 项目 | layout 格式 | paper 原文位置 | 备注 |
|---|---|---|---|
| `imp_genai-d4rt-v1` | per-paper md | `research/scene4d/feed_forward_tracker/docs/papers/<PaperName>/paper-raw.md` | 二手笔记在同目录的 `<PaperName>.md`。⚠ **`docs/` 被 `.gitignore` 屏蔽** → Glob / Grep 工具看不见，必须用 `Read` 精确路径或 `Bash ls` / `Bash grep` 绕开。 |
| `TrackingModel_Gallery` | legacy pdf+txt | `docs/papers_raw/*.{pdf,txt}` | 优先读 `.txt` 走 grep，看图表 / 公式时读 `.pdf` |

## `imp_genai-d4rt-v1` 特别约定

- 每个 paper 目录 `docs/papers/<PaperName>/` 下有两个核心 md：
  - `<PaperName>.md` —— 笔记 / 重点（user 个人整理，二手）
  - `paper-raw.md` —— **原文转录**（evidence 来源，一手）
- 本项目 scope = `docs/papers/` 下打了 `tracking` / `feed forward reconstruction` / `4D data` 三个 topic 的所有 paper（见 `docs/papers/topics/topic - *.md`）
- **paper 问题一律读 `paper-raw.md`**（不读 `<PaperName>.md` —— 那是二手）

## 触发

`rules/common/paper-evidence.md` 的"定位原文文件"段引用本文件，作为当前 cluster 的实证 lookup。

## 在新环境上的使用

如果新 host 上 clone 了 `imp_genai-d4rt-v1` 或 `TrackingModel_Gallery` 同名 repo，本表直接适用。
否则忽略，按 `rules/common/paper-evidence.md` 里的通用 layout 约定走。
