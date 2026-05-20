# optional/cluster-snippets/ — 仅 SLURM cluster 启用

## 触发条件

**仅在**目标 host 是 CoreWeave-style SLURM cluster（带 `sbatch` / `squeue` / `/mnt/data/` 共享存储 / conda env `imp_genai`）时才追加这些内容。

**Mac 跳过整个目录。**

## 包含什么

| 文件 | 内容 |
|---|---|
| `cluster-env.md` | SLURM hardware/partition 表 + GPU 选型 + resource 配比 + conda env 信息 + HF_HOME / shared paths + cluster-only safety rules + 合并的 `~/.claude/cluster_env.md` 全文 |
| `paper-evidence-projects.md` | `rules/common/paper-evidence.md` 的项目特定 lookup 附录（imp_genai-d4rt-v1 / TrackingModel_Gallery 等 paper 原文路径） |
| `skills/pyu-harness-setup-coreweave/` | 原 `pyu-harness-setup` skill（深度耦合 CoreWeave + conda env `imp_genai`）。CoreWeave 上 merge 到 `~/.claude/skills/pyu-harness-setup/` 即可。 |
| `memory/feedback_sbatch_active_monitor.md` | sbatch 后主动 tail log + squeue，不 passively wait |
| `memory/feedback_hardlink_vs_symlink_check.md` | shared storage 上 rm 之前用 `ls -la` 不是 `ls -i` 判 hard link |
| `memory/feedback_pyu_delete_no_size_probe.md` | `/pyu-delete` 时跳过 du/find，那正是它要绕过的慢操作 |

## Merge (仅 CoreWeave-compatible host)

```bash
# 1. 追加到 CLAUDE.md 末尾
cat ~/pyu-claude-all/optional/cluster-snippets/cluster-env.md >> ~/.claude/CLAUDE.md

# 2. paper-evidence 附录：放到 rules/common/ 旁边作为补充
cp ~/pyu-claude-all/optional/cluster-snippets/paper-evidence-projects.md ~/.claude/rules/common/

# 3. CoreWeave 版 harness skill
cp -r ~/pyu-claude-all/optional/cluster-snippets/skills/pyu-harness-setup-coreweave ~/.claude/skills/pyu-harness-setup
# 注意：去掉 -coreweave 后缀，保持 trigger keyword

# 4. memory feedback 拷到 project memory 目录
PROJ_MEM=~/.claude/projects/<your-project-hash>/memory
cp ~/pyu-claude-all/optional/cluster-snippets/memory/*.md $PROJ_MEM/
```

非 CoreWeave 环境：跳过本目录。改用 `core/skills-templates/pyu-harness-setup-generic/` 作为 harness skill 起点。

## 不要追加的情形

- ❌ mac
- ❌ 任何非 SLURM 集群（如纯 K8s）
- ❌ 任何 conda env 不叫 `imp_genai` 的环境（路径会错，规则会误导 Claude）

如果新 cluster 是 SLURM 但 conda env 不一样，先 fork cluster-env.md 改 env name 再追加。
