---
name: pyu-exp-team
description: >-
  v3 — Long-running monitor + auto-fix for SLURM experiments. Runs entirely in
  main session (no subagent spawning, no inter-agent SendMessage); main session
  acts as the orchestrator and "monitor" + "debugger" are inline subroutines
  driven by anomaly_class. Periodic execution via `/loop` wrapping —
  `ScheduleWakeup` self-paces ticks (300s in early phase, 1800s in loop phase,
  60s on freshly-failed). State persists in `~/0_pyu/exp-monitor/registry.json`
  + `~/0_pyu/exp-monitor/fix_log.json`. Auto-fix per whitelist of 9 anomaly
  classes; death-loop guard at fix_count ≥ 2.
  TRIGGER when: `/pyu-exp-team start <jobid>` / `/pyu-exp-team tick` (called
  by /loop) / `/pyu-exp-team add <jobid>` / `/pyu-exp-team status` /
  `/pyu-exp-team stop`. For long-term run, wrap with `/loop`:
  `/loop /pyu-exp-team tick` after a `start`.
  DO NOT TRIGGER when: user wants one-shot peek (use `/pyu-exp-monitor --once`).
origin: pyu-personal
---

# pyu-exp-team v3 — Main-session orchestrator (no subagents)

## What changed from v1 / v2

| | v1 (broken) | v2 (broken too) | v3 (works) |
|---|---|---|---|
| Architecture | 2 background `Agent({run_in_background:true})` named subagents | OMC team primitives `TeamCreate` + `Task(team_name=...)` | Main session inline; no subagents |
| Inter-comm | `general-purpose` lacks SendMessage → 不通 | Team members have SendMessage but team primitives untested in this harness | None needed; main session does both roles |
| Periodic loop | Spec'd ScheduleWakeup but never wired | Spec'd subagent self-pacing (untested) | `/loop /pyu-exp-team tick` + ScheduleWakeup chain |
| Tested? | NO (1 tick + dead) | NO (never invoked) | Designed to be testable: each subcommand is a single deterministic main-session action |

## Architecture

```
User: sbatch ... → jobid 7777
User: /pyu-exp-team start 7777          # init registry + do first tick (single shot)
User: /loop /pyu-exp-team tick           # enable periodic mode

   ┌────────── /loop dynamic mode ──────────┐
   │                                         │
   │   /pyu-exp-team tick (main session)    │
   │       │                                 │
   │       ├── read registry.json            │
   │       ├── for each running job:         │
   │       │     squeue, peek log,           │
   │       │     classify phase,             │
   │       │     scan anomalies              │
   │       │                                 │
   │       ├── for each new anomaly:         │
   │       │     do_fix(anomaly_class):      │
   │       │       lookup recipe             │
   │       │       Read sbatch/yaml/code     │
   │       │       Edit minimally            │
   │       │       Bash sbatch <path>        │
   │       │       write fix_log.json        │
   │       │       update registry chain     │
   │       │                                 │
   │       ├── write registry back           │
   │       │                                 │
   │       └── ScheduleWakeup(               │
   │              delaySeconds=<phase-aware>,│
   │              prompt="/pyu-exp-team tick"│
   │              reason=<phase summary>     │
   │           )  ← /loop fires this back    │
   │                                         │
   └─────────────────────────────────────────┘

When all jobs reach phase ∈ {done, failed-no-fix} →
  do NOT ScheduleWakeup → /loop chain ends naturally.
```

The "monitor" and "debugger" personas from v1/v2 collapse into **two inline subroutines** of one main-session tick: `do_tick()` and `do_fix(anomaly)`. No separate processes, no SendMessage. This is the only configuration we have evidence works in the harness.

## Files

```
~/0_pyu/exp-monitor/
├── registry.json     # current monitored jobs + per-job state
├── fix_log.json      # every auto-fix applied (audit trail)
└── reports/<jobid>.md  # per-job detailed tick log (optional, append-only)
```

### `registry.json` schema

```jsonc
{
  "schema_version": 3,
  "started_at": "2026-05-07T08:36:00Z",
  "jobs": {
    "1437882": {
      "sbatch_path":   "...",
      "name":          "da3_base_v1",
      "output_dir":    "...",
      "log_stdout":    "...",
      "started_at":    "2026-05-07T08:35:58Z",
      "phase":         "early",  // early | loop | done | failed | resubmitted_replaced
      "kind":          "train+eval",
      "milestones":    [],
      "anomalies":     [],       // historical, full
      "new_anomalies_this_tick": [],  // cleared after each tick
      "parent_jobid":  null,
      "fix_count":     0,        // chain length: # of fixes applied to root jobid
      "exp_dir":       null,
      "last_log_offset": 0,
      "last_tick_at":    null
    }
  }
}
```

## Subcommands (each = one main-session deterministic action)

### `start <jobid> [<jobid> ...]`

1. **Pre-checks** (Bash):
   - `mkdir -p ~/0_pyu/exp-monitor/reports`
   - `squeue -u $USER -j <jobid>` returns job (else fail clearly)

2. **Initialize registry.json** if missing; for each new jobid:
   - Resolve `sbatch_path` from `scontrol show job <id> | grep Command=`
   - Read sbatch text → extract `OUTPUT_DIR` / `--output` patterns → `output_dir`, `log_stdout`
   - Write entry with `phase=early, fix_count=0, parent_jobid=null`

3. **Do FIRST tick** inline (call `do_tick()` once)

4. **Tell user**:
   ```
   ✅ exp-team started for jobid <id>.
      registry: ~/0_pyu/exp-monitor/registry.json
      first tick done — phase=<X>, milestones=<list>
      To enable periodic monitoring + auto-fix:
          /loop /pyu-exp-team tick
      Or run one-off ticks anytime:
          /pyu-exp-team tick
   ```

### `tick`

Called by `/loop` periodically OR by user manually.

1. Run `do_tick()` (see below)
2. If active jobs remain (any with `phase ∉ {done, failed-no-fix, resubmitted_replaced}`):
   - Compute next-tick interval: `min` over per-job `interval_for_phase(p)`
     - early: 300s, loop: 1800s, just-failed: 60s
   - `ScheduleWakeup(delaySeconds=<min>, prompt="/pyu-exp-team tick", reason="<phase summary>")`
3. Else: do NOT schedule; report final summary; the `/loop` chain ends.

### `do_tick()` (inline subroutine, what each tick does)

For each running job in registry:

```python
# Pseudo-code; main session does this via Bash + Read tools
job = registry["jobs"][jobid]
state = check_squeue(jobid)
if state in {"COMPLETED", "FAILED"}:
    job["phase"] = "done" if exit_code == 0 else "failed-no-fix"
    continue

new_tail = read_log_from_offset(job["log_stdout"], job["last_log_offset"])
new_milestones = classify_milestones(new_tail)            # PHASE TABLE below
new_anomalies = scan_anomalies(new_tail)                  # ANOMALY TABLE below

job["milestones"] = job.get("milestones", []) + new_milestones
job["anomalies"]  = job.get("anomalies", [])  + new_anomalies
job["last_log_offset"] = new_offset
job["last_tick_at"]    = now_iso()

# Phase transition (training jobs):
if {"epoch0_val_done", "ckpt0_saved"} ⊆ set(job["milestones"]):
    job["phase"] = "loop"
if "train_done" in new_milestones:
    job["phase"] = "done"

# Auto-fix on new anomaly:
for a in new_anomalies:
    if job["fix_count"] >= 2:
        notify_user_refusal(jobid, a, reason="chain_too_long")
        job["phase"] = "failed-no-fix"
        continue
    new_jobid = do_fix(jobid, a, job)   # see do_fix subroutine
    if new_jobid:
        job["phase"] = "resubmitted_replaced"
        registry["jobs"][new_jobid] = make_child_entry(job, parent_jobid=jobid, fix_count=job["fix_count"]+1)

write_registry_atomic(registry)
print_tick_summary(registry)   # to user
```

### `do_fix(jobid, anomaly, job)` (inline subroutine, what each fix does)

```python
recipe = RECIPE_TABLE.get(anomaly["class"])
if recipe is None:
    notify_user_refusal(jobid, anomaly, reason="recipe_not_whitelisted")
    return None

try:
    diff = recipe.apply(job["sbatch_path"], anomaly, job)   # Read + Edit
    out = bash(f"cd /mnt/home/pengcheng.yu/code/selfEvo && sbatch {job['sbatch_path']}")
    new_jobid = parse_jobid_from_sbatch(out)
    append_fix_log_atomic(jobid, anomaly, recipe, diff, new_jobid, job["fix_count"])
    notify_user_success(jobid, new_jobid, anomaly, recipe, diff)
    return new_jobid
except Exception as e:
    notify_user_refusal(jobid, anomaly, reason=f"recipe_failed: {e}")
    return None
```

### `add <jobid>`

Append a new jobid to `registry.json` `"jobs"` map (resolve sbatch_path, output_dir like in `start`). Do NOT trigger immediate tick — next scheduled wake will pick it up.

### `status`

Read registry.json + fix_log.json + (per-job) tail of report. Print structured summary:

```
exp-team status @ <now>:
  Active jobs:
    1437882 (da3_base_v1)  phase=loop   milestones=[init, train, val0, ckpt0]  fix_count=0  last_tick=<5min ago>
    1437900 (da3_base_v1)  phase=early  parent=1437882  fix_count=1  ...
  Recent fixes (fix_log.json):
    1437882 → 1437900  oom → image_num_range backoff   2026-05-07T09:55:32Z
  /loop status: <active|stopped>
```

### `stop`

1. Mark all jobs as monitoring-stopped (does NOT scancel; just stop watching them):
   - Set `registry["jobs"][*]["phase"] = "monitoring_stopped"` (sentinel)
2. Next `/pyu-exp-team tick` invocation sees no running jobs → does NOT ScheduleWakeup → loop ends
3. Tell user:
   ```
   ⏹  exp-team stopped. Registry preserved at ~/0_pyu/exp-monitor/registry.json (audit).
       /loop will end on its next wake (within next ScheduleWakeup interval).
       Jobs themselves are NOT canceled. Use `scancel <jobid>` if you want that.
   ```

## PHASE TABLE (training jobs)

| Marker (in new tail bytes) | Milestone added | Phase rule |
|---|---|---|
| `imp_genai environment activated!` | `init_ok` | phase=early |
| `Start training epoch 0` | `train_started` | phase=early |
| `[selfEvo Val ep0]` | `epoch0_val_done` | (toward loop) |
| `Saved state for global step <iters_per_epoch>` | `ckpt0_saved` | (toward loop) |
| both `epoch0_val_done` AND `ckpt0_saved` seen | — | phase=early → loop |
| `[Phase 2]` / `Aggregating results` / `[DONE]` | `train_done` | phase=done after final |
| any traceback / FAILED / sbatch error | (anomaly) | phase=failed (anomaly handler decides) |

## ANOMALY TABLE (regex on new tail)

| Regex | anomaly_class |
|---|---|
| `^Traceback`, `^\[rank\d+\]: Traceback` | `python_exception` |
| `RuntimeError: element 0 of tensors does not require grad` | `autograd_no_grad` |
| `ValueError: Tried to step \d+ times. The specified number of total steps is \d+` | `scheduler_total_steps` |
| `Key '\w+' is not in struct` | `hydra_struct` |
| `CUDA out of memory` | `oom` |
| `NCCL.*timeout`, `Watchdog caught collective operation timeout` | `nccl_timeout` |
| `ChildFailedError`, `multiprocessing\.errors\.ChildFailedError` | `ddp_child_died` |
| `FileNotFoundError`, `No such file or directory` | `missing_path` |
| log unchanged > 30 min on running job | `stalled` |

## RECIPE TABLE (auto-fix whitelist; ≤2 fixes per chain)

| Class | Recipe | Action |
|---|---|---|
| `hydra_struct` | `add_plus_prefix` | grep sbatch for unprefixed `<key>=` from anomaly_line → Edit `<key>=` → `++<key>=` → resubmit |
| `missing_path` | `migrate_pyu_to_scene4d` | if path matches `/mnt/data/pyu/omniWorld/*` → migrate to `/mnt/data/scene4d/Omni/*` per migration table; else surface |
| `scheduler_total_steps` | `revert_num_epoch` | revert sbatch's `++train.num_epoch=N` to original; resubmit |
| `autograd_no_grad` | `wrap_enable_grad` | grep code for offending function → Edit wrap with `with torch.enable_grad():` → resubmit |
| `oom` | `backoff_image_num_range` | sbatch override: `++train.image_num_range=[X-4, Y-4]` AND `++train.max_img_per_gpu=Y-4` → resubmit (2× cap) |
| `nccl_timeout` | `resubmit_with_resume` | resubmit unchanged + `++train.resume=<latest_ckpt>` |
| `ddp_child_died` | `recurse_to_known_class` | parse rank-0 traceback → recurse classification; if maps, apply recipe; else surface |
| `python_exception` | `match_subclass` | text-match: `not in struct` → hydra_struct; `out of memory` → oom; else surface |
| `stalled` | `scancel_resubmit_with_resume` | scancel <jobid> + resubmit + `++train.resume=<latest_ckpt>` |

## Death-loop guard

```python
def chain_length(jobid, registry):
    n = 0
    cur = jobid
    while cur and cur in registry["jobs"] and registry["jobs"][cur].get("parent_jobid"):
        n += 1
        cur = registry["jobs"][cur]["parent_jobid"]
    return n

if chain_length(jobid, registry) >= 2:
    refuse_with_full_chain_history()
```

## Notification format (printed to user in main session)

### Tick summary (every tick):

```markdown
📊 [pyu-exp-team] Tick @ <YYYY-MM-DDTHH:MM:SSZ>:
   Jobs:
     1437882 (da3_base_v1)  phase=loop   milestones=[init, train, val0, ckpt0]  no anomaly
     1437900 (da3_base_v1)  phase=early  parent=1437882
   Anomalies this tick: 0
   Next tick: in 1800s (loop phase) → /pyu-exp-team tick
```

### Auto-fix success:

```markdown
🔧 [pyu-exp-team] Auto-fix applied (chain len 1/2):
   Job 1437882 → 1437900 (resubmitted)
   Class: oom
   Recipe: backoff_image_num_range
   Anomaly line: `CUDA out of memory at ...`
   Diff: slurm/da3/train_and_eval_base.sbatch:60
       added `++train.image_num_range=[16,34] ++train.max_img_per_gpu=34`
   Log: ~/0_pyu/exp-monitor/fix_log.json[1437882]
```

### Auto-fix refused:

```markdown
⚠️  [pyu-exp-team] Cannot auto-fix:
   Job 1437900
   Class: ddp_child_died (no rank-0 traceback found)
   Reason: recipe_not_whitelisted
   Action: surfaced for user review.
   Log: ~/0_pyu/exp-monitor/fix_log.json[1437900]
```

## File I/O atomicity

All registry / fix_log writes use Python + `fcntl.flock`:

```python
import json, fcntl, os
path = os.path.expanduser("~/0_pyu/exp-monitor/registry.json")
with open(path, "r+") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    data = json.load(f)
    # ... modify ...
    f.seek(0); f.truncate()
    json.dump(data, f, indent=2)
    fcntl.flock(f, fcntl.LOCK_UN)
```

## Boundaries

- Skill body NEVER refactors model.py / loss.py / dataset.py for hypothetical bugs.
- Only Edit sbatch / yaml / `0_test_vis/*.py` / `eval/configs/*.yaml` files for direct anomaly fixes.
- Always Read before Edit (per global memory rule).
- Death-loop guard is hard: ≥2 fixes in chain → refuse.
- Skill body NEVER scancels jobs unless the recipe says so (`stalled`).
- Skill body NEVER deletes registry / fix_log; user clears manually.

## Limitations (v3)

- Conversation-scoped: `/loop` chain dies when conversation ends. Restart = `/pyu-exp-team start <jobid>` again (registry preserves state).
- Single-user, single-machine.
- Read-only auto-fixes: only adjusts sbatch / yaml / hydra overrides.
- Whitelist-only auto-fix.

## Example end-to-end

```
User: sbatch slurm/da3/train_and_eval_base.sbatch
SLURM: Submitted batch job 1438000

User: /pyu-exp-team start 1438000
main session:
  → mkdir -p ~/0_pyu/exp-monitor/reports
  → squeue -j 1438000 → RUNNING
  → resolved sbatch_path, output_dir, log_stdout
  → wrote registry.json
  → do_tick() → phase=early, milestones=[init_ok]
  → ✅ exp-team started for jobid 1438000.

User: /loop /pyu-exp-team tick

[5 min later — /loop fires /pyu-exp-team tick]
main session:
  → do_tick() → tail log, phase=early still (val ep0 not yet seen), no anomaly
  → ScheduleWakeup(300s, "/pyu-exp-team tick", reason="early")
  → 📊 [pyu-exp-team] Tick @ ... Jobs: 1438000 phase=early milestones=[init_ok, train_started] no anomaly. Next: 300s.

[10 min later — next tick]
main session:
  → do_tick() → val ep0 + ckpt0 seen, phase=loop
  → ScheduleWakeup(1800s, "/pyu-exp-team tick", reason="loop")
  → 📊 ...

[35 min after that — next tick during epoch 3]
main session:
  → do_tick() → tail shows "ChildFailedError ... rank 4 OOM"
  → anomaly.class=oom
  → do_fix(1438000, oom, job):
      Read sbatch → Edit add `++train.image_num_range=[16,34] ++train.max_img_per_gpu=34`
      Bash: sbatch ... → Submitted batch job 1438050
      append_fix_log
  → registry: 1438000.phase=resubmitted_replaced, 1438050 added with parent=1438000, fix_count=1
  → 🔧 [pyu-exp-team] Auto-fix applied (chain len 1/2): 1438000 → 1438050 ...
  → ScheduleWakeup(300s, ..., reason="early (new fixed job)")
```

## What this skill body does NOT do

- Does NOT spawn `Agent({run_in_background:true})` (v1 fail mode)
- Does NOT use `TeamCreate / Task(team_name=)` primitives (v2 untested)
- Does NOT rely on inter-agent SendMessage (the harness limitation that broke v1+v2)
- Does NOT need a ScheduleWakeup outside of `/loop` mode (so wrapping with `/loop` is required for periodic execution)
