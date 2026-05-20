---
name: feedback-pyu-delete-no-size-probe
description: "When running /pyu-delete, NEVER run `du -sh` / `find | wc -l` on the target before submit — this is the exact slow op pyu-delete exists to bypass."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ac6f4db-1a12-4b5c-a456-dce3451f4b24
---

`/pyu-delete` 的目标本来就是 TB 级 + 百万级文件，**在 login node 上做 `du -sh <target>` 本身就要 10-30+ 分钟**（NFS 全树 metadata 遍历）—— 跟"用 pyu-delete 加速删除"自相矛盾。

**Why**: 2026-05-18 一次 `/pyu-delete ~/0_del` 中，我先按 skill 的 step-3 跑 `du -sh + find | wc -l`，user 等 1 分钟没结果指出问题；停掉后我又去跑 `du -sh` 量 top-3 subdir，user 再次纠正"我真的服了"。两次都是同一个错误：**为了"看清楚"目标而做了 skill 设计上要避开的慢 op**。

**How to apply**:
- 收到 `/pyu-delete` → **跳过** skill SKILL.md 里 step-3 的 `du -sh` 和 `find | wc -l`。这些是 "nice-to-show" 不是 "must-have"。
- 必要的快速侦查 only：`ls <target>` (顶层 child 名字 + 数量，秒级)。**不**追问哪个 subdir 占用更多 —— worker 内部 adaptive-depth manifest 会自己处理 structure；user 看 child 名字就知道要删什么。
- 直接生成 sbatch，展示给 user，等 "yes" 提交。
- Worker 默认 4 节点 × 32 ranks = 128 并发对任何 size target 都够；不需要 user 端先估大小再调参数。
- 同理：删除前**不**做 `du` 拿 baseline 与删除后比对（删干净了 ls 一下就知道，不需要数字）。
- 同理：清理大 NFS 目录前 user 主动让你 du 估容量 → 也要劝阻或告知风险（"NFS du 全树要几十分钟，要不要先 ls 看看顶层结构？"）。

**唯一例外**：user 明确要求"先告诉我有多大再删" → 跑，但**告知预计时长** + run_in_background，让 user 决定是否值得等。
