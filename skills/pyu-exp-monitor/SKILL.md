---
name: pyu-exp-monitor
description: >-
  Periodic monitor for live sbatch experiments on the SLURM cluster (training
  + evaluation). Tracks each running job by JOBID → originating .sbatch script
  → expected output dir, parses the log to classify lifecycle phase, and reports
  state at an adaptive cadence: every 5 min during the EARLY phase
  (initialization + first complete `train + val + log + ckpt-save` cycle for
  training jobs, or first 10 sequences inferred for eval jobs); every 30 min
  thereafter during the STEADY-LOOP phase. On any anomaly (traceback, NCCL
  failure, OOM, missing-file, dead-job-no-progress) → record + report only.
  No auto-fix, no auto-resubmit. Self-paces via ScheduleWakeup.
  TRIGGER when: user invokes `/pyu-exp-monitor`, asks to "watch / monitor /
  babysit / 看一下 / 监控" a SLURM job by id or name, or asks to track all
  running selfEvo / DA3 / Pi3 / VGGT experiments.
  DO NOT TRIGGER when: user wants a one-shot peek (`squeue` / `tail logs/X.out`
  is enough) without periodic re-checks; or when no jobs are running for the
  user (squeue returns empty).
origin: pyu-personal
---

# pyu-exp-monitor — Adaptive SLURM Experiment Monitor

Watch live sbatch jobs, classify lifecycle phase from the stdout log, report
progress + anomalies. Adaptive cadence (5 min early / 30 min loop). Records to
the per-experiment log if the job is linkable to `experiments/<slug>/`,
otherwise to a fallback registry under `~/0_pyu/exp-monitor/`.

## Mental Model

A single skill invocation = **one tick**. Each tick:

1. Discover or refresh the registry of monitored jobs
2. For each job: query `sacct` / `squeue`, peek the log tail, classify phase, diff against last tick's state
3. Write progress entry; flag anomalies
4. Schedule the next tick via `ScheduleWakeup` based on the most aggressive phase across all monitored jobs (early > loop)

The skill **never auto-fixes**, **never auto-resubmits**, **never modifies code or sbatch files**. Reporting only.

## Inputs

- `<jobid>` (positional) — monitor only that job, otherwise auto-discover from `squeue -u $USER`
- `--sbatch <path>` — explicit binding for jobs whose sbatch isn't auto-resolvable
- `--once` — one tick, no rescheduling (manual peek)
- Default: auto-discover all of `$USER`'s running/pending jobs whose name starts with `da3_` / `pi3_` / `vggt_` / `selfEvo_` / `pyu_`

## Registry

State lives at `~/0_pyu/exp-monitor/registry.json`:

```jsonc
{
  "1437549": {
    "sbatch_path": "/mnt/home/pengcheng.yu/code/selfEvo/slurm/da3/smoke_train_val_eval.sbatch",
    "name": "da3_smoke_full_20260507_072452",
    "output_dir": "src/selfEvo-DA3/training/outputs/da3_smoke_full_20260507_072452",
    "log_stdout": "slurm/da3/logs/da3_smoke_full-1437549.out",
    "started_at": "2026-05-07T07:24:52Z",
    "kind": "train+eval",        // train | eval | train+eval | sanity
    "phase": "early",            // early | loop | done | failed
    "last_tick_at": "2026-05-07T07:31:05Z",
    "last_log_offset": 12834,    // bytes; for incremental tail
    "milestones": ["init_ok", "train_started", "epoch0_train_done", "epoch0_val_done", "ckpt0_saved"],
    "anomalies": [],
    "exp_dir": null              // experiments/<slug>/ if linkable, else null
  }
}
```

Registry is read+rewritten atomically every tick (small file, no locking issues for single-user single-machine).

## How a Tick Works

### 1. Refresh job set

```bash
squeue -u $USER -h -o "%i|%j|%T|%M"
sacct -u $USER --starttime now-2hours --format=JobID,JobName,State,Elapsed -P -n
```

For each running/pending job: ensure registry entry exists (create with auto-discovered fields). For each registry entry not in current squeue: classify as `done` or `failed` via `sacct ExitCode` and stop scheduling for it.

### 2. Resolve sbatch ↔ output ↔ log

For a fresh job, walk these in order until one yields the sbatch path:
- `--sbatch` flag value
- `scontrol show job <id> | grep Command=` (literal sbatch path SLURM has on file)
- Match `JobName` against `slurm/**/*.sbatch` headers (`#SBATCH --job-name=<name>`)

For output dir + log: read the sbatch text and extract `OUTPUT_DIR`, `--output`, `OUTPUT_BASE` patterns. Common sites in selfEvo:
- Training: `src/selfEvo-DA3/training/outputs/${NAME}/`
- Eval: `eval/outputs_*/<exp>/`
- Stdout: `slurm/da3/logs/<name>-<jobid>.out`

If sbatch references `experiments/<YYYY-MM-DD-slug>/` either by path or by aggregator script (e.g. `experiments/2026-05-06-da3-base-experiment/aggregate_eval.py`), bind `exp_dir` so reports go to that dir's `notes.md`.

### 3. Classify phase

Parse log tail (incremental from `last_log_offset` to EOF). Phase decision tree:

#### Training jobs (`kind ∈ {train, train+eval, sanity}`)

| Marker found in log (newest occurrence) | Phase becomes | Milestone added |
|---|---|---|
| `imp_genai environment activated!` | `early` | `init_ok` |
| `Start training epoch 0` | `early` | `train_started` |
| `Epoch: [0]  [0/N]` | `early` | (progress) |
| `Saved state for global step` (epoch ≥ 1) | `loop` | `ckpt<N>_saved` |
| `[selfEvo Val ep0]` | `early` | `epoch0_val_done` |
| `Saved state for global step <N>` where N == iters_per_epoch | `early` | `ckpt0_saved` |
| `[Phase B]`, `[Phase 2]`, `Aggregating results` | `loop` | `train_done` |
| `[DONE]`, `Training time` | `done` | `finished` |
| Any `Traceback / Error / FAILED` line | `failed` | (anomaly) |

→ **`early` = before `epoch0_val_done` AND `ckpt0_saved` both seen.** Once both seen → flip to `loop`.

#### Eval jobs (`kind == eval`)

| Marker | Phase | Milestone |
|---|---|---|
| `Loaded DA3 from <ckpt>` | `early` | `model_loaded` |
| `[N/M] Sequence <id> processed` where N ≥ 10 | `loop` | `eval_10seq` |
| `Average pose estimation metrics` / `<dataset>-metric*.csv saved` | `done` | `metric_written` |
| `[DONE] all <K> evals SUCCEEDED` | `done` | `all_done` |
| Traceback / FAILED | `failed` | (anomaly) |

### 4. Anomaly detection

Per tick, scan **the new tail bytes** (since `last_log_offset`) for patterns. Each match → append to `anomalies[]` with `{first_line, line_no, classification, suggested_root_cause}`. **Do not fix, do not act.**

| Regex | Classification | Suggested root cause (just text in report) |
|---|---|---|
| `^Traceback`, `^[rank\d+]: Traceback` | `python_exception` | parse the final exception class + message |
| `RuntimeError: element 0 of tensors does not require grad` | `autograd_no_grad` | likely `@torch.no_grad()` covers code that needs grad |
| `ValueError: Tried to step \d+ times. The specified number of total steps is \d+` | `scheduler_total_steps` | OneCycleLR baked total_steps; resume changed num_epoch |
| `Key '\w+' is not in struct` | `hydra_struct` | needs `++<key>=...` override |
| `CUDA out of memory` | `oom` | reduce `image_num_range[1]` or `max_img_per_gpu` |
| `NCCL.*timeout`, `Watchdog caught collective operation timeout` | `nccl_timeout` | one rank slow / hung; check per-rank logs |
| `ChildFailedError`, `multiprocessing.errors.ChildFailedError` | `ddp_child_died` | one worker exited early; root cause in earlier traceback |
| `FileNotFoundError`, `No such file or directory` | `missing_path` | check path in code/yaml |
| `slurm_load_jobs error: Invalid job id` | `job_disappeared` | job already exited |
| Log unchanged > 30 min on running job | `stalled` | job alive but not progressing |

### 5. Cadence: schedule next tick

Compute next-tick interval per job, then take min:

| Job phase | Interval |
|---|---|
| `early` | 300s |
| `loop` | 1800s |
| `failed` (just caught) | 60s next tick to confirm log + collect final state, then stop |
| `done` | (remove from active set) |

If active set empty → don't reschedule, end.
Otherwise → `ScheduleWakeup({delaySeconds: <min interval>, prompt: "<original /pyu-exp-monitor invocation>", reason: "<phase summary>"})`

### 6. Report

For each job, append to `<exp_dir>/notes.md` if bound, else `~/0_pyu/exp-monitor/<jobid>.md`:

```markdown
## Tick 2026-05-07T07:36:05Z (phase=early, elapsed=11m21s)

### Progress
- New milestones since last tick: `epoch0_val_done`, `ckpt0_saved`
- Latest log line: `[Phase B] Post-train eval: 1 ckpt × {videodepth, relpose} × {Geo, Video} on 4 GPUs...`

### Metrics seen this tick (if any)
- `[selfEvo Val ep0] depth_l1=0.0785  rot=1.750deg  trans=5.381deg`

### Anomalies
- (none)

### Next check at: 2026-05-07T07:41:05Z (5min, early phase)
```

If anomalies exist, **also** print a top-of-conversation alert (not just write the file) so the user sees it inline.

### 7. Final-state summary

When job transitions to `done` or `failed`, write a closing entry:

```markdown
## FINAL 2026-05-07T07:32:35Z — state=done, ExitCode=0:0, total=7m43s
- All milestones: init_ok → train_started → epoch0_train_done → epoch0_val_done → ckpt0_saved → train_done → all_done
- Output: src/selfEvo-DA3/training/outputs/da3_smoke_full_20260507_072452/
- Wandb: https://wandb.ai/impossible-ai/selfEvo-DA3/runs/0j3vid4u
- Anomalies (lifetime): 0
```

## Files in This Skill

- `SKILL.md` — this file
- (no helper scripts in v1; everything inlined as bash via the harness)

## Boundaries / Non-goals

- **Read-only**: never edits code, sbatch, or yaml. If a fix is obvious, mention it in the report and stop.
- **Never auto-resubmits**: if a job dies, the report tells the user how to recover but does not run `sbatch` again.
- **Never cancels jobs**: `scancel` is always user-initiated.
- **Per-user, single-machine state**: registry is local; no shared lock; if the user runs `/pyu-exp-monitor` twice in parallel sessions, the second invocation overwrites the registry — accepted limitation.
- **Token frugal**: each tick reads only the tail bytes since `last_log_offset` (typical: 1-50 KB), not the whole log. Registry caps total `anomalies` length per job at ~20 entries.

## Example Invocation

```
User: /pyu-exp-monitor

Claude:
  → squeue -u $USER → 1 running job (1437549, da3_smoke_full)
  → resolved sbatch: slurm/da3/smoke_train_val_eval.sbatch
  → output_dir: src/selfEvo-DA3/training/outputs/da3_smoke_full_20260507_072452/
  → log: slurm/da3/logs/da3_smoke_full-1437549.out
  → tail since last (offset=0): 12834 bytes, classified phase=early
  → milestones: init_ok, train_started, epoch0_val_done, ckpt0_saved
  → anomalies: 0
  → wrote ~/0_pyu/exp-monitor/1437549.md
  → next tick in 300s (5 min, early phase)
  [ScheduleWakeup invoked with delaySeconds=300]
```

On the second auto-fired tick (5 min later), if Phase B has started and a few seqs have processed:

```
  → tail since offset=12834: 47210 new bytes, phase=loop (eval_10seq seen)
  → milestones added: phase_b_started, eval_10seq
  → next tick in 1800s (30 min, loop phase)
```

If a tick catches an exception:

```
  → tail since offset=...: anomaly detected — python_exception
    Traceback ... RuntimeError: element 0 of tensors does not require grad
    Suggested root cause: autograd_no_grad — @torch.no_grad() covers code needing grad
  → wrote anomaly entry to <log>
  → next tick in 60s (failure-confirmation tick)
```
