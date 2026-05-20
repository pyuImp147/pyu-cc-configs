---
name: sbatch jobs must be actively monitored, not waited on passively
description: After any sbatch submission, must actively poll log+squeue, fix errors and resubmit on the fly — never sit idle waiting for the job to finish "successfully"
type: feedback
originSessionId: 74552aa8-9e94-468c-be9a-7734367f3188
---
After submitting any sbatch job, NEVER passively wait for completion. Always set up active monitoring:
- poll `squeue -j <jobid>` for state
- tail the stdout/stderr log (`logs/*.out`, `logs/*.err`)
- look for python tracebacks, missing-path errors, or premature exits — jobs can crash within seconds of starting and you'd never know if you wait
- if anomaly detected → diagnose → fix code/sbatch → cancel old job → resubmit → continue monitoring
- only stop monitoring when job actually reaches `COMPLETED` or user explicitly says stop

**Why:** User explicitly told me on 2026-05-11 after observing me ScheduleWakeup-then-do-nothing patterns. Their words: "每次提交过sbatch之后你需要根据log 监控job运行状态，出现任何问题解决+重新提交，而不是空等. 任务可能早就出错退出." Jobs can fail silently in seconds — passive waiting wastes hours of wall-clock + cluster time.

**How to apply:** When a workflow involves sbatch:
- Always pair `sbatch <script>` with a follow-up monitoring loop (`/loop` + `ScheduleWakeup`, or a custom tick subroutine)
- First tick should fire within 60-180s of submission to catch fail-fast errors
- Distinguish "expected internal errors" (e.g. OOM cells in a benchmark sweep where OOM IS the measurement target) from "job-level fatal errors" (python traceback outside try/except, missing file, sbatch syntax)
- Never just `sbatch ...; echo "submitted, will report when done"` — that's the failure mode user is warning against
- For pure tooling-fit considerations: `pyu-exp-team` is training-tuned (OOM=anomaly, hydra override recipes) and not appropriate for benchmark workflows where OOM is intentional. Default to custom `/loop` monitor for non-training jobs.
