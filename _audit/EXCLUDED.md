# EXCLUDED — 排除清单与理由

Generated: 2026-05-20
源端列表来自 `ls -la ~/.claude/` + `find ~/.claude -maxdepth 2 -type d`

## 1. Runtime state（**永不**同步 — 含会话历史 / 缓存 / 临时文件）

| 路径（源 host） | 理由 |
|---|---|
| `~/.claude/sessions/` | 单次 session 状态 |
| `~/.claude/session-data/` | 单次 session 数据 |
| `~/.claude/session-env/` | 单次 session env |
| `~/.claude/projects/` | 项目级 session 历史（但 `projects/<hash>/memory/` 已被 cherry-pick 同步对应 .md，目录本身排除） |
| `~/.claude/tasks/` | Task state |
| `~/.claude/teams/` | Team state |
| `~/.claude/history.jsonl` | 历史 jsonl |
| `~/.claude/bash-commands.log` | bash 命令日志（~2.8MB） |
| `~/.claude/cost-tracker.log` | 成本日志（~3MB） |
| `~/.claude/checkpoints.log` | checkpoint 日志 |
| `~/.claude/.session-stats.json` | session 统计 |
| `~/.claude/.session-stats.json.tmp.*` | tmp 文件 |
| `~/.claude/stats-cache.json` | 统计缓存 |
| `~/.claude/cache/` | 通用缓存 |
| `~/.claude/paste-cache/` | 粘贴缓存 |
| `~/.claude/shell-snapshots/` | shell 快照 |
| `~/.claude/file-history/` | 文件历史 |
| `~/.claude/backups/` | 自动备份 |
| `~/.claude/downloads/` | 下载缓存 |
| `~/.claude/homunculus/` | OMC homunculus state |
| `~/.claude/metrics/` | 指标 |
| `~/.claude/ide/` | IDE state（也是 mode=700 secret-like） |
| `~/.claude/.last-cleanup` | cleanup 时间戳 |
| `~/.claude/CLAUDE.md.backup.*` | CLAUDE.md 历史备份（保留原始 .md 即可） |

## 2. Secrets（**永不**同步 — 含 token / 鉴权 / 个人凭证）

| 路径 | 理由 |
|---|---|
| `~/.claude/.credentials.json` | 用户认证凭证（mode=600） |
| `~/.claude/policy-limits.json` | 政策限制（mode=600） |
| `~/.claude/mcp-needs-auth-cache.json` | MCP 鉴权缓存 |

## 3. ECC / OMC 安装产物（**跳过** — 用户手动重装会自动恢复）

| 路径 | 理由 |
|---|---|
| `~/.claude/plugins/` | 整个 plugin 系统 (ECC + karpathy + OMC 等) |
| `~/.claude/.omc/` | OMC runtime state |
| `~/.claude/.omc-config.json` | OMC config |
| `~/.claude/ecc/` | ECC install state |
| `~/.claude/marketplace.json` | plugin marketplace |
| `~/.claude/plugin.json` | plugin manifest |
| `~/.claude/PLUGIN_SCHEMA_NOTES.md` | plugin schema 参考 |
| `~/.claude/.agents/` | OMC 内部 agents 集 |
| `~/.claude/hud/` | OMC HUD |
| `~/.claude/skills/` (大批 156-6=**150 项** ECC/OMC plugin skills) | OMC/ECC 重装会装回 |
| `~/.claude/agents/*.md` (42 项 ECC personas) | ECC 重装会装回。包含 build-error-resolver / code-architect / code-reviewer / security-reviewer / tdd-guide 等所有 ECC 标配 persona |
| `~/.claude/commands/*.md` (76 项 ECC slash commands) | ECC 重装会装回。包含 build-fix / code-review / cpp-build / docs / e2e / loop-start / orchestrate / plan / promote / quality-gate / refactor-clean / save-session / skill-create 等 |

> 注：原 `~/.claude/AGENTS.md`（顶层）也归为 ECC 装的，跳过。

## 4. Host-specific config（**用户主动放弃**复刻 — Round 2 决定）

| 路径 | 理由 | 复刻成本 |
|---|---|---|
| `~/.claude/settings.json` | 含绝对路径 hook 引用 (`/mnt/home/pengcheng.yu/.claude/scripts/hooks/*.js`) + cluster permissions (如 `rm -rf /mnt/data*`) + env vars。新 host 需重新累积。 | 新环境上 ECC/OMC 重装 + 自然交互 1-2 周累积出大部分必要 allow/deny |
| `~/.claude/settings.local.json` | Project-local override，host-specific | 重新生成 |
| `~/.claude/hooks/hooks.json` | hook 配置入口 | ECC 重装提供默认 |
| `~/.claude/scripts/` | hook 脚本 + lib + orchestrate 脚本 (大部分是 ECC 装的) | ECC 重装提供 |
| `~/.claude/mcp-configs/` | MCP server 配置 | 重新配置 (含 token) |

## 5. Cluster-only doc（**已合并到 cluster snippet** — 不重复同步）

| 路径 | 处理 |
|---|---|
| `~/.claude/cluster_env.md` | 全文已并入 `optional/cluster-snippets/cluster-env.md`。原文件**不**单独同步，避免双源。 |

## 6. Auto-regenerated index files（**有意不同步** — Claude 自动重建）

| 路径 | 处理 |
|---|---|
| `~/.claude/memory/MEMORY.md` | 顶层 auto-memory index，Claude 新 host 启动会按 feedback 文件自动重建。同步反而易过时。 |
| `~/.claude/projects/<hash>/memory/MEMORY.md` | 项目级 auto-memory index，同上 |

## 7. 其他

| 路径 | 理由 |
|---|---|
| `~/.claude/README.md` | ECC bundle 自带（项目说明），重装会回 |
| `~/.claude/the-security-guide.md` | ECC bundle 自带 |

## Sanity check（在源 host 跑一次确认本清单覆盖全部）

```bash
# 列源 host 上的 top-level 项
ls -la ~/.claude/ | awk '{print $NF}' | sort > /tmp/source.lst
# 对照本 MANIFEST + EXCLUDED 是否每一项都覆盖
```
