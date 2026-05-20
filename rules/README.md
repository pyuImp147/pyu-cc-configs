# rules/ — 必须复刻：跨项目准则

## 包含什么

| 子目录 | 文件数 | 内容 |
|---|---|---|
| `common/` | 12 | coding-style / testing / security / git-workflow / development-workflow / code-review / hooks / agents / patterns / performance / paper-evidence / README |
| `python/` | 5 | coding-style / testing / security / patterns / hooks (Python 专属) |

源 = `~/.claude/rules/common/` + `~/.claude/rules/python/`

## 与 ECC 装的 rules 的关系

ECC 重装后会**自动写**一份 `~/.claude/rules/` 的默认副本到磁盘。建议：
- 先 ECC 重装（写默认）
- 再 `cp -rn` 本 repo 内容（`-n` = no-clobber，**不**覆盖 ECC 默认）
- 然后 diff 看是否有需要 merge 的差异

如果想让本 repo 内容**强制覆盖** ECC 默认（确认本 repo 的版本就是最新的）：

```bash
cp -rf ~/pyu-claude-all/rules/common ~/.claude/rules/
cp -rf ~/pyu-claude-all/rules/python ~/.claude/rules/
```

## paper-evidence.md 特别说明

`rules/common/paper-evidence.md` 含项目特定路径（`imp_genai-d4rt-v1` 的 `paper-raw.md` 位置 + `TrackingModel_Gallery` 的 `papers_raw/`）。在新 host 上：
- 如果对应项目存在 → 路径会自然 resolve
- 如果不存在 → 规则的核心约束（"读原文 + 给 evidence block"）依然生效，只是 project-specific shortcut 不再适用。**不需要改文件**。

## 与 CLAUDE.md 的连接

`core/CLAUDE.md` 里 `## Paper Questions` 末尾引用 `~/.claude/rules/common/paper-evidence.md` 全文。本 module 必须在 `core/CLAUDE.md` merge 之后或之前 merge，确保引用不悬空。
