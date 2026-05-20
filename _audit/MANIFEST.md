# MANIFEST — Synced Inventory

Generated: 2026-05-20
Source host: CoreWeave cluster, `/mnt/home/pengcheng.yu/.claude/`
Total files: ~40 (excluding `.git/`, `.gitignore`)

## core/

| Target path (in this repo) | Source path | Why portable |
|---|---|---|
| `core/CLAUDE.md` | `~/.claude/CLAUDE.md` (slice: OMC 块以外 + SLURM 块以外，Paper Questions 项目特定 lookup 已挪出) | 人格 / Tooling / Language / Philosophy / Core Principles / Explanation Guideline / Paper Questions (通用) / Documentation / Safety / Tool gotchas |
| `core/memory/feedback_md_toc.md` | `~/.claude/memory/feedback_md_toc.md` | Markdown TOC 偏好规则 — 跨环境通用（项目路径 reference 已 genericize） |
| `core/memory/feedback_data_convention_direct_test.md` | `~/.claude/projects/-mnt-home-pengcheng-yu-code/memory/` | 数据约定要 raw→physical 闭环测试 — 跨环境通用 |
| `core/skills-templates/pyu-harness-setup-generic/SKILL.md` | 基于原 `pyu-harness-setup` 抽象 | env-agnostic 版 harness bootstrap skill；剥离 CoreWeave / conda env `imp_genai` 假设 |
| `core/README.md` | (新写) | Module 文档 |

## rules/

| Target | Source | Why portable |
|---|---|---|
| `rules/common/coding-style.md` | `~/.claude/rules/common/coding-style.md` | 跨语言/项目通用 |
| `rules/common/testing.md` | 同上目录 | 同 |
| `rules/common/security.md` | 同 | 同 |
| `rules/common/git-workflow.md` | 同 | 同 |
| `rules/common/development-workflow.md` | 同 | 同 |
| `rules/common/code-review.md` | 同 | 同 |
| `rules/common/hooks.md` | 同 | 同 |
| `rules/common/agents.md` | 同 | 同 |
| `rules/common/patterns.md` | 同 | 同 |
| `rules/common/performance.md` | 同 | 同 |
| `rules/common/paper-evidence.md` | 同 | 已 genericize：项目特定 lookup 移到 `optional/cluster-snippets/paper-evidence-projects.md` |
| `rules/python/coding-style.md` | `~/.claude/rules/python/coding-style.md` | Python 通用 |
| `rules/python/testing.md` | 同 | 同 |
| `rules/python/security.md` | 同 | 同 |
| `rules/python/patterns.md` | 同 | 同 |
| `rules/python/hooks.md` | 同 | 同 |
| `rules/README.md` | (新写) | Module 文档 |

## skills/ (env-agnostic user-authored only)

| Target | Source | SLURM 依赖 | mac 可用? |
|---|---|---|---|
| `skills/pyu-delete/` | `~/.claude/skills/pyu-delete/` | 强 (sbatch) | ❌ |
| `skills/pyu-exp-monitor/` | `~/.claude/skills/pyu-exp-monitor/` | 强 (squeue) | ❌ |
| `skills/pyu-exp-team/` | `~/.claude/skills/pyu-exp-team/` | 强 | ❌ |
| `skills/pyu-traj-vis/` | `~/.claude/skills/pyu-traj-vis/` | 无 | ✅ |
| `skills/README.md` | (新写) | - | - |

> `pyu-harness-setup` 已 fork：env-agnostic 骨架在 `core/skills-templates/pyu-harness-setup-generic/`；原 CoreWeave 深耦合版在 `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/`。

筛选方法（source check）:
```bash
comm -23 <(ls ~/.claude/skills/ | sort) \
         <(find ~/.claude/plugins/cache -mindepth 3 -maxdepth 5 -type d -name skills -exec ls {} \; | sort -u)
# 输出 6 项：5 个 pyu-* + 1 个 learned (后者是空目录，不同步)
# pyu-harness-setup 因深度耦合 CoreWeave，从 skills/ 移到 cluster-snippets/skills/ + 抽象到 core/skills-templates/
```

## optional/cluster-snippets/

| Target | Source | 何时使用 |
|---|---|---|
| `optional/cluster-snippets/cluster-env.md` | `~/.claude/CLAUDE.md` SLURM 块 (L95-L139) + `~/.claude/cluster_env.md` 全文 + Safety 中 `/mnt/...` 两条 | 仅 SLURM cluster |
| `optional/cluster-snippets/paper-evidence-projects.md` | 从 `rules/common/paper-evidence.md` 拆出的项目特定 lookup（imp_genai-d4rt-v1 / TrackingModel_Gallery） | 仅 CoreWeave host（有对应项目 worktree） |
| `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/` | `~/.claude/skills/pyu-harness-setup/` 原版 + `CLUSTER_NOTE.md` | 仅 CoreWeave（深度耦合 conda env `imp_genai` + 共享盘约定） |
| `optional/cluster-snippets/memory/feedback_sbatch_active_monitor.md` | `~/.claude/projects/-mnt-home-pengcheng-yu-code/memory/` | 仅 SLURM cluster (sbatch 强相关) |
| `optional/cluster-snippets/memory/feedback_hardlink_vs_symlink_check.md` | 同上目录 | 仅 cluster (shared storage 场景) |
| `optional/cluster-snippets/memory/feedback_pyu_delete_no_size_probe.md` | 同 | 仅 cluster (/pyu-delete 仅 SLURM 有意义) |
| `optional/cluster-snippets/README.md` | (新写) | Module 文档 |

## Top-level

| Target | Source |
|---|---|
| `README.md` | (新写) |
| `.gitignore` | (新写) — 防 runtime 垃圾 |
| `_audit/MANIFEST.md` | (你正在看) |
| `_audit/EXCLUDED.md` | (新写) |

## 同步范围合规检查

- [x] 4 个 env-agnostic user-authored skills 在 `skills/`；1 个 CoreWeave 深耦合 skill (`pyu-harness-setup`) fork 为 generic + coreweave 两版
- [x] 12 个 common rules + 5 个 python rules；`paper-evidence.md` 已 genericize（项目特定 lookup 进 cluster snippet）
- [x] CLAUDE.md 已拆分：portable 部分 → `core/CLAUDE.md`；cluster 部分 → `optional/cluster-snippets/cluster-env.md`；项目特定 Paper Questions lookup → `optional/cluster-snippets/paper-evidence-projects.md`
- [x] Memory 文件按 cluster-coupled / portable 拆分到 core/ vs optional/；`feedback_md_toc.md` 中 `imp_genai-d4rt-v1` reference 已 genericize
- [x] cluster_env.md 全文已并入 cluster snippet
- [x] OMC 自动管理块（`<!-- OMC:START --> ... <!-- OMC:END -->`）已剔除（OMC 重装会写回）
- [x] `MEMORY.md` (auto-memory index) 不同步 — Claude 在新 host 自动重建
- [x] `.gitignore` 防 runtime 垃圾 + secrets + `.omc/`
- [x] 无 `__pycache__/` 残留
- [x] **二次 audit grep**：portable 区无 `imp_genai` / `CoreWeave` / `sbatch` / `/mnt/data` / `/mnt/home` / `/opt/conda` 的实质性引用（仅剩下指向 cluster snippet 的"see X"指针）
