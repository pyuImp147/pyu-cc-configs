# MANIFEST — Synced Inventory

Generated: 2026-05-20
Source host: CoreWeave cluster, `/mnt/home/pengcheng.yu/.claude/`
Total files: ~40 (excluding `.git/`, `.gitignore`)

## core/

| Target path (in this repo) | Source path | Why portable |
|---|---|---|
| `core/CLAUDE.md` | `~/.claude/CLAUDE.md` (slice: OMC 块以外 + SLURM 块以外) | 人格 / Tooling / Language / Philosophy / Core Principles / Explanation Guideline / Paper Questions / Documentation / Safety / Tool gotchas — 跨 host 通用工作习惯 |
| `core/memory/MEMORY.md` | `~/.claude/projects/-mnt-home-pengcheng-yu-code/memory/MEMORY.md` | 项目级 auto-memory index（保留与 feedback 文件的引用关系） |
| `core/memory/MEMORY-legacy.md` | `~/.claude/memory/MEMORY.md` | 早期顶层 memory（与项目级不同，含 markdown style feedback 引用） |
| `core/memory/feedback_md_toc.md` | `~/.claude/memory/feedback_md_toc.md` | Markdown TOC 偏好规则 — 跨环境通用 |
| `core/memory/feedback_data_convention_direct_test.md` | `~/.claude/projects/-mnt-home-pengcheng-yu-code/memory/` | 数据约定要 raw→physical 闭环测试 — 跨环境通用 |
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
| `rules/common/paper-evidence.md` | 同 | 含项目路径但规则核心跨环境（private repo 保留） |
| `rules/python/coding-style.md` | `~/.claude/rules/python/coding-style.md` | Python 通用 |
| `rules/python/testing.md` | 同 | 同 |
| `rules/python/security.md` | 同 | 同 |
| `rules/python/patterns.md` | 同 | 同 |
| `rules/python/hooks.md` | 同 | 同 |
| `rules/README.md` | (新写) | Module 文档 |

## skills/ (user-authored only)

| Target | Source | SLURM 依赖 | mac 可用? |
|---|---|---|---|
| `skills/pyu-harness-setup/` | `~/.claude/skills/pyu-harness-setup/` | 弱 | ✅ |
| `skills/pyu-delete/` | `~/.claude/skills/pyu-delete/` | 强 (sbatch) | ❌ |
| `skills/pyu-exp-monitor/` | `~/.claude/skills/pyu-exp-monitor/` | 强 (squeue) | ❌ |
| `skills/pyu-exp-team/` | `~/.claude/skills/pyu-exp-team/` | 强 | ❌ |
| `skills/pyu-traj-vis/` | `~/.claude/skills/pyu-traj-vis/` | 无 | ✅ |
| `skills/README.md` | (新写) | - | - |

筛选方法（source check）:
```bash
comm -23 <(ls ~/.claude/skills/ | sort) \
         <(find ~/.claude/plugins/cache -mindepth 3 -maxdepth 5 -type d -name skills -exec ls {} \; | sort -u)
# 输出 6 项：5 个 pyu-* + 1 个 learned (后者是空目录，continuous-learning 尚未沉淀，不同步)
```

## optional/cluster-snippets/

| Target | Source | 何时使用 |
|---|---|---|
| `optional/cluster-snippets/cluster-env.md` | `~/.claude/CLAUDE.md` SLURM 块 (L95-L139) + `~/.claude/cluster_env.md` 全文 + Safety 中 `/mnt/...` 两条 | 仅 SLURM cluster |
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

- [x] 5 个 user-authored skills 全部包含（源端有 6 项但 `learned/` 为空目录，跳过）
- [x] 12 个 common rules + 5 个 python rules，全部包含
- [x] CLAUDE.md 已拆分：portable 部分 → `core/CLAUDE.md`；cluster 部分 → `optional/cluster-snippets/cluster-env.md`
- [x] Memory 文件按 cluster-coupled / portable 拆分到 core/ vs optional/
- [x] cluster_env.md 全文已并入 cluster snippet
- [x] OMC 自动管理块（`<!-- OMC:START --> ... <!-- OMC:END -->`）已剔除（OMC 重装会写回）
- [x] `.gitignore` 防 runtime 垃圾 + secrets
- [x] 无 `__pycache__/` 残留
