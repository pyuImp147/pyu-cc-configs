# Mac Setup — Read this if you're Claude Code on a fresh mac

> **Audience**: 你（Claude Code）在 user 的 mac 上，user 刚 clone 了这个 repo，希望你按本文档自动 merge 三层 portable 配置到 `~/.claude/`。
>
> **Source of truth**: `~/pyu-claude-all/README.md` (full design) + 本文档（mac 专属操作流程）。
>
> **执行原则**：
> 1. 每一步 verify 后再走下一步；不要批量 cp 失败就 silent skip。
> 2. 不覆盖已存在的文件（`cp -n`），先告诉 user 冲突情况让 ta 决定。
> 3. cluster-coupled 内容（`optional/cluster-snippets/`）一律 **不动**。
> 4. 全程报告每一步实际做了什么，不要默认成功。

---

## 前置假设

User 已经手动装好 ECC + OMC（`omc setup` 或等价流程），所以：
- `~/.claude/` 存在
- `~/.claude/CLAUDE.md` 含 `<!-- OMC:START --> ... <!-- OMC:END -->` 块
- `~/.claude/skills/` 含 plugin-managed skills（ECC/OMC 自带的 150+ 个）
- `~/.claude/rules/` 可能含 ECC 默认 rules（或为空）

如果上面任一不成立，**停下来**告诉 user 先做 ECC + OMC 安装。

---

## Step 0 — Sanity check

跑这一组，把结果汇报给 user，**不要**继续做任何事直到 user 看完确认：

```bash
# 0a. ECC/OMC 是否装好
test -d ~/.claude && echo "~/.claude OK" || echo "~/.claude MISSING — abort"
test -d ~/.claude/plugins && echo "plugins/ OK (ECC/OMC installed)" || echo "plugins/ MISSING — install ECC+OMC first"
test -f ~/.claude/CLAUDE.md && wc -l ~/.claude/CLAUDE.md || echo "CLAUDE.md missing"

# 0b. repo clone 位置
test -d ~/pyu-claude-all && echo "repo at ~/pyu-claude-all" || echo "repo NOT at ~/pyu-claude-all — ask user where"

# 0c. 已经 merge 过的检测（避免重复 append）
grep -q '## Identity$' ~/.claude/CLAUDE.md 2>/dev/null && echo "CLAUDE.md ALREADY has portable section (re-run scenario)" || echo "CLAUDE.md is fresh — safe to append"

# 0d. 已经 cp 过的 skills？
ls ~/.claude/skills/ 2>/dev/null | grep -E '^pyu-' || echo "no pyu-* skills yet"
```

**汇报给 user**，等回应。

如果 0c 显示 ALREADY → 询问 user 要不要跳过 CLAUDE.md append（避免追加两次）。
如果 0d 显示已有 pyu-* → 询问要不要覆盖（默认跳过）。

---

## Step 1 — Merge CLAUDE.md (portable global instructions)

```bash
# 追加到现有 ~/.claude/CLAUDE.md 末尾（OMC 块之后）
cat ~/pyu-claude-all/core/CLAUDE.md >> ~/.claude/CLAUDE.md
```

**Verify**:

```bash
tail -20 ~/.claude/CLAUDE.md   # 应该看到 "## Tool usage gotchas" 段（CLAUDE.md 的尾巴）
grep -c '^## Identity$' ~/.claude/CLAUDE.md   # 应该 == 1
grep -c '^## Tool usage gotchas' ~/.claude/CLAUDE.md   # 应该 == 1
```

如果 grep count > 1 → user 重复跑了，告诉 ta 并提供回滚指引：`vim ~/.claude/CLAUDE.md` 手动删一份。

**Mac 上不追加 cluster snippet** — `optional/cluster-snippets/cluster-env.md` 不要 cat。

---

## Step 2 — Merge rules/

```bash
# common rules (12 files)
cp -rn ~/pyu-claude-all/rules/common ~/.claude/rules/

# python rules (5 files)
cp -rn ~/pyu-claude-all/rules/python ~/.claude/rules/
```

**Verify**:

```bash
ls ~/.claude/rules/common/ | wc -l   # 应该 >= 12（ECC 可能装了别的，>= 即可）
ls ~/.claude/rules/python/ | wc -l   # 应该 >= 5
ls ~/.claude/rules/common/paper-evidence.md && echo "paper-evidence OK"
```

**不要 cp** `optional/cluster-snippets/paper-evidence-projects.md`（CoreWeave 专属）。

如果 ECC 已经装了同名 rule 且内容不同 → `cp -n` 会跳过。让 user 决定要不要手动 diff + merge：

```bash
diff ~/pyu-claude-all/rules/common/paper-evidence.md ~/.claude/rules/common/paper-evidence.md
```

---

## Step 3 — Merge user-authored skills

```bash
# 4 个 env-agnostic skills（直接拷）
cp -r ~/pyu-claude-all/skills/pyu-delete       ~/.claude/skills/
cp -r ~/pyu-claude-all/skills/pyu-exp-monitor  ~/.claude/skills/
cp -r ~/pyu-claude-all/skills/pyu-exp-team     ~/.claude/skills/
cp -r ~/pyu-claude-all/skills/pyu-traj-vis     ~/.claude/skills/

# pyu-harness-setup: 用 generic 版（mac 上不用 coreweave 版）
cp -r ~/pyu-claude-all/core/skills-templates/pyu-harness-setup-generic \
      ~/.claude/skills/pyu-harness-setup
# 注意 destination 是 pyu-harness-setup（不带 -generic 后缀），保持 trigger keyword
```

**Verify**:

```bash
ls ~/.claude/skills/ | grep -E '^pyu-' | sort
# 应该看到（exactly 5）：
# pyu-delete
# pyu-exp-monitor
# pyu-exp-team
# pyu-harness-setup
# pyu-traj-vis

head -5 ~/.claude/skills/pyu-harness-setup/SKILL.md
# 第一行的 name: 应该是 pyu-harness-setup-generic（来源标识，不影响 trigger）
# 如果你介意命名一致，可以 sed -i '' 's/name: pyu-harness-setup-generic/name: pyu-harness-setup/' ~/.claude/skills/pyu-harness-setup/SKILL.md
```

**预期失效**（告诉 user，不是 bug）：
- `pyu-delete` / `pyu-exp-monitor` / `pyu-exp-team` 调起会报错 — 它们要 `sbatch` / `squeue`，mac 上没有
- `pyu-traj-vis` 要 `pip install viser` 才能跑
- `pyu-harness-setup` (generic 版) 应该可正常 trigger deep-interview

---

## Step 4 — Memory (auto-memory)

```bash
# 4a. 先让 Claude Code 在 user 常用的工作目录跑一次，生成 projects/<hash>/memory/
# 这步 user 已经在用的话可以跳过——如果 CC 之前在 ~/code（或别的 dir）跑过，
# ~/.claude/projects/<encoded-hash>/memory/ 就已经存在了

# 列已有的 project memory 目录
ls -d ~/.claude/projects/*/memory 2>/dev/null
```

询问 user：想把 portable feedback 拷到哪个 project memory？

得到目标 PROJ_MEM 后：

```bash
PROJ_MEM=~/.claude/projects/<选定的-hash>/memory
mkdir -p $PROJ_MEM
cp ~/pyu-claude-all/core/memory/feedback_md_toc.md $PROJ_MEM/
cp ~/pyu-claude-all/core/memory/feedback_data_convention_direct_test.md $PROJ_MEM/

# 不拷 MEMORY.md（Claude 启动会按 feedback 文件自动重建 index）
# 不拷 optional/cluster-snippets/memory/（SLURM-only feedback）
```

**Verify**:

```bash
ls $PROJ_MEM | grep feedback
# 应该至少看到这 2 个 .md
```

---

## Step 5 — 最终汇报

把以下结果作为完成总结贴给 user：

```bash
echo "=== Merge complete ==="
echo "CLAUDE.md size: $(wc -l < ~/.claude/CLAUDE.md) lines"
echo "Rules:  $(ls ~/.claude/rules/common 2>/dev/null | wc -l) common, $(ls ~/.claude/rules/python 2>/dev/null | wc -l) python"
echo "User skills: $(ls ~/.claude/skills/ | grep -E '^pyu-' | wc -l) (expected 5)"
echo "Memory feedback synced to: $PROJ_MEM"
```

然后告诉 user：

1. **重启 Claude Code session**（让新的 CLAUDE.md 加载）
2. 试一下：`/pyu-harness-setup --at /tmp/test-harness 测试项目` 应该触发 deep-interview
3. 试一下：和 Claude 说 "请用 Top-Down 风格解释一下 transformer attention"，看 ta 是否走 Explanation Guideline 的格式
4. 如果哪里不符合预期 → `~/pyu-claude-all/README.md` 看 design intent，或回 cluster 跟原版 `~/.claude/CLAUDE.md` 对照

---

## Step 6 — 不要做的事

- ❌ 不要 cat `optional/cluster-snippets/cluster-env.md` 进 CLAUDE.md（SLURM/conda 内容在 mac 上是噪音）
- ❌ 不要 cp `optional/cluster-snippets/skills/pyu-harness-setup-coreweave/` 到 skills/（深度耦合 CoreWeave）
- ❌ 不要 cp `optional/cluster-snippets/paper-evidence-projects.md` 到 rules/（项目特定 lookup，mac 上对应项目不存在）
- ❌ 不要 cp `optional/cluster-snippets/memory/feedback_*.md`（SLURM-only feedback）
- ❌ 不要 cp `core/memory/MEMORY.md`（不存在了，因为是 auto-regenerated）
- ❌ 不要动 `~/.claude/settings.json` / `~/.claude/hooks/` — user 主动放弃复刻这层，mac 上自然累积

---

## Step 7 — 回滚指引（如果 user 不满意）

```bash
# 1. CLAUDE.md 回滚：手动编辑去掉追加的部分
#    （追加段是从 "<!-- User customizations (portable) -->" 到 EOF）
vim ~/.claude/CLAUDE.md

# 2. Skills 撤销
rm -rf ~/.claude/skills/pyu-{delete,exp-monitor,exp-team,traj-vis,harness-setup}

# 3. Rules 撤销
#    不要 rm -rf rules/common/ 整个目录 — ECC 装的也在里面
#    只删本 repo 同步进去的：
diff -r ~/pyu-claude-all/rules/common ~/.claude/rules/common | grep "^Only in /mnt/home/pengcheng.yu/pyu-claude-all" | awk '{print $NF}'
# 然后 rm 这些文件
```

---

## 自检 checklist（merge 完后 Claude 自查一遍）

- [ ] `~/.claude/CLAUDE.md` 含 `## Identity` 段且只出现 1 次
- [ ] `~/.claude/CLAUDE.md` **不**含 `## SLURM Cluster (CoreWeave)` 段
- [ ] `~/.claude/CLAUDE.md` **不**含 `imp_genai` 字符串（mac 上不应有）
- [ ] `~/.claude/skills/` 含 `pyu-harness-setup/` 且其 SKILL.md 顶部 description 是 generic 版（`ENV-AGNOSTIC skeleton`）而**不是** `for a new research project on the CoreWeave cluster`
- [ ] `~/.claude/rules/common/paper-evidence.md` 内**不**含 `imp_genai-d4rt-v1` 字符串

如果有 ❌ → 报告 user 哪里不符合，给出 root cause 推断。
