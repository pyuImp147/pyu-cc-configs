# core/ — 必须复刻：portable 全局指令 + auto-memory

## 包含什么

| 文件 | 源（当前 cluster） | 内容 |
|---|---|---|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` 里 OMC 块**之外**、SLURM 块**之外**的部分 | Identity / Tooling / Language / Philosophy / Core Principles / Explanation Guideline / Paper Questions / Documentation / Safety / Tool usage gotchas |
| `memory/feedback_md_toc.md` | `~/.claude/memory/feedback_md_toc.md` | markdown TOC 偏好（跨环境通用） |
| `memory/feedback_data_convention_direct_test.md` | `~/.claude/projects/-mnt-home-pengcheng-yu-code/memory/` | data convention 验证准则（跨环境通用） |
| `skills-templates/pyu-harness-setup-generic/` | (新写，基于原 pyu-harness-setup 抽象) | env-agnostic 版 harness bootstrap skill；CoreWeave 版在 `optional/cluster-snippets/skills/` |

> `MEMORY.md` (auto-memory index) **不**同步。Claude 在新 host 上启动后会按目录里的 feedback 文件**自动重建** index，预先拷一份反而易过时。

## 不包含什么（移到 cluster snippet 或被排除）

- ❌ `~/.claude/CLAUDE.md` 顶部的 `<!-- OMC:START --> ... <!-- OMC:END -->` 块 → OMC 重装时自动写回，**不同步**
- ❌ `## SLURM Cluster (CoreWeave)` 整段 (L95-L139) → 移到 `optional/cluster-snippets/cluster-env.md`
- ❌ `## Safety` 里 `/mnt/data/` 与 `/mnt/home/pengcheng.yu/` 两条 → 移到 cluster snippet
- ❌ cluster-only feedback (`feedback_sbatch_active_monitor.md` / `feedback_hardlink_vs_symlink_check.md` / `feedback_pyu_delete_no_size_probe.md`) → 移到 cluster snippet
- ❌ `MEMORY.md` 顶层 index → 不同步，由 Claude 在新 host 自动重建

## Merge 到新 host

```bash
# CLAUDE.md：追加到现有 ~/.claude/CLAUDE.md（OMC 块之后）
cat ~/pyu-claude-all/core/CLAUDE.md >> ~/.claude/CLAUDE.md

# Memory：合并到项目级 memory 目录
# 注：CC 把 auto-memory 按 cwd 哈希成 ~/.claude/projects/<hash>/memory/
# 在新 host 上你的项目路径不同，对应的 hash 也不同。
# 处理方法：
#   1) 启动一次 CC 让它生成对应 projects/<hash>/memory/ 目录
#   2) 把 core/memory/ 下的 .md 拷到那个目录
PROJ_MEM=~/.claude/projects/<your-project-hash>/memory
mkdir -p $PROJ_MEM
cp ~/pyu-claude-all/core/memory/*.md $PROJ_MEM/
```

## 与 cluster snippet 的关系

- portable 的 `CLAUDE.md` 里有引用：
  > Cluster / SLURM / conda specifics 在 `optional/cluster-snippets/cluster-env.md`
- 在 cluster 上 merge 时，**必须**接着 `cat optional/cluster-snippets/cluster-env.md >> ~/.claude/CLAUDE.md`。
- 在 mac 上 **不要** cat cluster snippet。

## 预期失效模式

- `Paper Questions` 现在只含通用规则；项目特定 lookup（`imp_genai-d4rt-v1` / `TrackingModel_Gallery`）已挪到 `optional/cluster-snippets/paper-evidence-projects.md`，只在 CoreWeave 环境 cat 进来。
- `Documentation` 里提到 `selfEvo doc rewrite cycles` —— 是历史 lesson learned 记录，跨环境通用。
- `Tool usage gotchas` 里讲 Edit/Write 必须 Read —— 是 Claude Code 通用 harness 行为，所有 host 都适用。
