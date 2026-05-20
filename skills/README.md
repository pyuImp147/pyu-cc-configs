# skills/ — 必须复刻：用户自写 skills

## 包含什么

仅同步**不在 ECC/OMC plugin cache 里**的 skill（= 你手写的）。源端校验方式：

```bash
comm -23 <(ls ~/.claude/skills/ | sort) \
         <(find ~/.claude/plugins/cache -mindepth 3 -maxdepth 5 -type d -name skills -exec ls {} \; | sort -u)
```

在源 cluster 上跑这条命令的结果是 6 项。**裁切后**：
- `learned/` 是空目录（continuous-learning v2 还没沉淀出 instinct），不同步
- `pyu-harness-setup/` 深度耦合 CoreWeave + conda env `imp_genai`，**fork 为两版**：
  - 原版 → `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/`（仅在 CoreWeave 上 merge）
  - 环境无关骨架 → `core/skills-templates/pyu-harness-setup-generic/`（mac / 其他 cluster 用）

本目录下保留的是**剩余 4 个**用户自写 skill：

| Skill | SLURM 依赖 | mac 上能跑? | 说明 |
|---|---|---|---|
| `pyu-delete` | **强**（sbatch 多节点并行 rm） | ❌ 报错 | 高并发删除 SLURM 集群上大目录树 |
| `pyu-exp-monitor` | **强**（squeue + scontrol） | ❌ 报错 | SLURM 实验监控 |
| `pyu-exp-team` | **强**（squeue + auto-fix sbatch） | ❌ 报错 | 长时运行 + 自动 fix 失败 SLURM job |
| `pyu-traj-vis` | 无 | ✅ 可跑 | viser 3D pointmap + trajectory visualization |

## Merge

```bash
# 直接 cp，与 ECC 装的 skill 不会重名（plugin skills 在 ~/.claude/plugins/cache/，
# 而 user-authored 在 ~/.claude/skills/，两个不同目录）
cp -r ~/pyu-claude-all/skills/* ~/.claude/skills/
```

## 预期失效模式

- pyu-delete / pyu-exp-monitor / pyu-exp-team 在 mac 上**调起即报错**（找不到 `sbatch` / `squeue` / `scontrol`）—— 这是预期行为，不要把它们删掉，回到 cluster 还要用。

## 校验

在新 host 上 `ls ~/.claude/skills/` 应该看到 4 个新增条目（本目录）+ 1 个 `pyu-harness-setup`（从 generic 或 coreweave 版本之一拷贝）。`/pyu-harness-setup` slash command 在 cluster 和 mac 上都应该能起，触发 deep-interview 流程。
