# pyu-cc-configs — Portable Claude Code Configuration Bundle

跨 host 复刻当前 CoreWeave cluster 上 `~/.claude/` 内**与 cluster/conda 环境无关**的 Claude Code 配置（人格 + 跨项目准则 + 自定义 skill）。

> **要在 mac 上 setup？** 把 `MAC_SETUP.md` 喂给 Claude Code，让它按步骤帮你 merge。一行：`Read ~/pyu-claude-all/MAC_SETUP.md and execute it`。

源 host：CoreWeave SLURM cluster (`/mnt/home/pengcheng.yu/.claude/`)
目标 host：新 cluster / 本地 mac
Repo: `git@github.com:pyuImp147/pyu-cc-configs.git` (**private**)

---

## 设计哲学

1. **不做自动安装**：不提供 `install.sh`。每个 module 独立一个 README，user 按需 `cp` / `cat >>`。
2. **不复刻 ECC / OMC**：plugin 层在新 host 上重装（`omc setup` / ECC 重装），会自带 plugin 默认 skills/agents/commands/hooks/rules。本 repo 只补 plugin 装不到的"个人层"。
3. **不复刻 hooks / settings.json**：这些是 host-coupled（绝对路径、cluster permissions），新 host 上重新累积，不强求开箱即用。
4. **Private repo + 保留 PII**：username / email / 绝对路径都保留原样。不脱敏。
5. **Cluster-coupled 内容独立成 snippet**：放 `optional/cluster-snippets/`，仅 SLURM cluster 上 `cat >>` 追加。Mac 上跳过。

---

## 目录结构

```
~/pyu-claude-all/
├── README.md                   ← 你正在看
├── core/                       ← MUST replicate
│   ├── README.md
│   ├── CLAUDE.md                ← portable 全局指令（已去除 SLURM / cluster / imp_genai 块）
│   ├── memory/                  ← portable feedback (markdown style / data convention test)
│   └── skills-templates/
│       └── pyu-harness-setup-generic/  ← env-agnostic 版 harness bootstrap
├── rules/                      ← MUST replicate
│   ├── common/                  ← 12 个跨语言/跨项目 rule docs (paper-evidence 已 genericized)
│   └── python/                  ← 5 个 Python 专属 rule docs
├── skills/                     ← MUST replicate (user-authored, env-agnostic 部分)
│   ├── pyu-delete/             ← SLURM-only runtime（mac 上仅定义存在）
│   ├── pyu-exp-monitor/        ← SLURM-only runtime
│   ├── pyu-exp-team/           ← SLURM-only runtime
│   └── pyu-traj-vis/           ← 跨环境可用
├── optional/
│   └── cluster-snippets/       ← 仅 CoreWeave 环境启用
│       ├── README.md
│       ├── cluster-env.md       ← SLURM/conda/HF_HOME/shared paths
│       ├── paper-evidence-projects.md  ← imp_genai-d4rt-v1 / TrackingModel_Gallery 项目 lookup
│       ├── skills/
│       │   └── pyu-harness-setup-coreweave/  ← 原 pyu-harness-setup，CoreWeave 深耦合版
│       └── memory/              ← cluster-specific feedback (sbatch/hardlink/...)
└── _audit/
    ├── MANIFEST.md             ← 每个被同步的文件 + 源路径 + 分类
    └── EXCLUDED.md             ← 每个被刻意排除的项 + 原因
```

---

## 新环境 merge 顺序

### A. 新 SLURM cluster

```bash
# 1. 安装 ECC + OMC（手动）
omc setup     # or whatever the latest install flow is
# ECC 重装会带回 plugin-managed skills/agents/commands/hooks/rules

# 2. clone this repo
git clone git@github.com:pyuImp147/pyu-cc-configs.git ~/pyu-claude-all

# 3. CLAUDE.md = portable 主体 + cluster snippet
# 注意：~/.claude/CLAUDE.md 此时已包含 OMC 自动注入的块（<!-- OMC:START --> ... <!-- OMC:END -->）
# 在 OMC 块下方追加我们的 portable 主体 + cluster snippet：
cat ~/pyu-claude-all/core/CLAUDE.md >> ~/.claude/CLAUDE.md
cat ~/pyu-claude-all/optional/cluster-snippets/cluster-env.md >> ~/.claude/CLAUDE.md

# 4. Rules
cp -rn ~/pyu-claude-all/rules/common ~/.claude/rules/
cp -rn ~/pyu-claude-all/rules/python ~/.claude/rules/
# paper-evidence 项目特定附录（CoreWeave 才需要）
cp ~/pyu-claude-all/optional/cluster-snippets/paper-evidence-projects.md ~/.claude/rules/common/

# 5. 自定义 skills（4 个 env-agnostic 的 + CoreWeave 版 harness）
cp -r ~/pyu-claude-all/skills/* ~/.claude/skills/
cp -r ~/pyu-claude-all/optional/cluster-snippets/skills/pyu-harness-setup-coreweave ~/.claude/skills/pyu-harness-setup

# 6. Memory
PROJ=~/.claude/projects/-mnt-home-<user>-<workdir>/memory
mkdir -p $PROJ
cp ~/pyu-claude-all/core/memory/*.md $PROJ/
cp ~/pyu-claude-all/optional/cluster-snippets/memory/*.md $PROJ/
# 注：MEMORY.md 不需要拷贝 — Claude 启动时会自动按目录里 feedback 重建 index
```

### B. 本地 mac

```bash
# 1. 安装 ECC + OMC（手动）
omc setup

# 2. clone
git clone git@github.com:pyuImp147/pyu-cc-configs.git ~/pyu-claude-all

# 3. CLAUDE.md = portable 主体（不加 cluster snippet）
cat ~/pyu-claude-all/core/CLAUDE.md >> ~/.claude/CLAUDE.md

# 4. Rules
cp -rn ~/pyu-claude-all/rules/common ~/.claude/rules/
cp -rn ~/pyu-claude-all/rules/python ~/.claude/rules/
# 不要拷 paper-evidence-projects.md（那是 CoreWeave 专属）

# 5. 自定义 skills (4 个 env-agnostic 的 + generic 版 harness skeleton)
# 注意: pyu-delete / pyu-exp-monitor / pyu-exp-team 依赖 SLURM，mac 上调起会报错（预期）
cp -r ~/pyu-claude-all/skills/* ~/.claude/skills/
cp -r ~/pyu-claude-all/core/skills-templates/pyu-harness-setup-generic ~/.claude/skills/pyu-harness-setup

# 6. Memory
PROJ=~/.claude/projects/<your-project-key>/memory
mkdir -p $PROJ
cp ~/pyu-claude-all/core/memory/*.md $PROJ/
# 不加 optional/cluster-snippets/memory/，不加 MEMORY.md（auto-regenerated）
```

---

## Module 详细说明

每个 module 子目录下都有 README.md，说明：
- 源在 cluster 上的位置
- merge 到 `~/.claude/` 的具体命令
- 是否依赖 cluster snippet
- 预期失效模式（如有）

直接看：
- `core/README.md`
- `rules/README.md`（沿用上游 rules/README.md，本目录是其子集）
- `skills/README.md`
- `optional/cluster-snippets/README.md`

---

## 审计

- `_audit/MANIFEST.md` —— 每个被同步的文件 + 源路径 + 为什么算 portable
- `_audit/EXCLUDED.md` —— runtime state / secrets / ECC-OMC 安装产物 / cluster-only 项的排除清单

打开两份文件检查 sanity，确认没有泄漏 runtime / secret 到 repo。
