# Why this is in cluster-snippets/

This is the **original** `pyu-harness-setup` skill, which is deeply coupled to:
- CoreWeave SLURM cluster (`h100` / `rtxp6000` partitions)
- Conda env `imp_genai`
- Shared paths `/mnt/data/` (read-only) and `/mnt/home/pengcheng.yu/` (personal)
- Project naming convention `imp_genai-<branch>` for monorepo worktrees
- `activate.sh` entry point + `HF_HOME` cache

如果你的目标 host 是这套 cluster 环境，直接用本 skill 即可。

如果不是（mac / 别的 cluster / 别的 conda env），用 `core/skills-templates/pyu-harness-setup-generic/` 那个 env-agnostic 骨架版本，按你自己环境补 compute integration pattern。

## Merge 到新 cluster（CoreWeave-compatible）

```bash
cp -r ~/pyu-claude-all/optional/cluster-snippets/skills/pyu-harness-setup-coreweave ~/.claude/skills/pyu-harness-setup
```

注意改回 `pyu-harness-setup` 这个名字（不要带 `-coreweave` 后缀），保持原 trigger keyword 一致。

## Merge 到非 CoreWeave 环境

不要拷本目录。改拷 generic 版：
```bash
cp -r ~/pyu-claude-all/core/skills-templates/pyu-harness-setup-generic ~/.claude/skills/pyu-harness-setup
```

按需在 `<your-project>/.claude/rules/` 下加你环境的 compute rule（`slurm.md` / `k8s.md` / 等）。
