---
name: pyu-delete
description: >-
  High-throughput parallel deletion of a directory tree on the SLURM cluster.
  Submits a multi-node × multi-process sbatch job that round-robin partitions
  the target's children among ranks and removes them concurrently. Performs
  permission/safety checks (owner, blacklist, symlink resolve) BEFORE submit,
  shows the user the generated .sbatch + a target summary (file count / size),
  and only auto-submits after explicit "yes".
  TRIGGER when: user invokes `/pyu-delete [path]`, or asks to "delete /
  rm -rf / wipe / clean out" a directory under their cluster home or
  scratch space and wants speed (large tree / millions of files).
  DO NOT TRIGGER when: deletion target is a single small file, or path is
  outside `/mnt/home/<user>` and `/mnt/data/<user>-owned` areas, or user just
  wants a `rm` one-liner. Refuse outright for `/`, `/mnt`, `/mnt/data`,
  `/mnt/home`, `$HOME` itself, or any path not owned by the invoking user.
origin: pyu-personal
---

# pyu-delete — Parallel SLURM Deletion

Wipes everything **inside** a target directory (the directory itself is preserved unless `--remove-root` is given) using a multi-node × multi-process SLURM job. Designed for the case where `rm -rf` on the login node would take hours; cluster has plenty of CPU + parallel filesystem bandwidth.

## When to Use

- Deleting large dataset staging directories (millions of files, hundreds of GB / TB)
- Cleaning out checkpoint dumps, intermediate features, archive expansions
- User says "remove everything under X fast" / "rm -rf is too slow" / "wipe X"

## When NOT to Use

- Single file deletion → just `rm` on login node
- Target outside the user's owned space → refuse, report safety violation
- Network mount or external storage where parallel deletes hurt other users → ask first

## Defaults

| Knob | Default | Override |
|---|---|---|
| Path | `/mnt/home/pengcheng.yu/0_del` | positional `[path]` arg |
| Partition | `rtxp6000` | `--partition h100` |
| Nodes | 4 | `--nodes N` |
| Tasks/node | 32 | `--ntasks-per-node N` |
| CPUs/task | 2 | `--cpus-per-task N` |
| Mem/node | 64G | `--mem N` |
| Time limit | 4:00:00 | `--time HH:MM:SS` |
| Remove root dir | no | `--remove-root` |
| Confirm flow | show sbatch + du+find summary, await `yes` | (always) |

## Invocation Flow (what Claude does)

When user types `/pyu-delete [path]` (or asks to wipe a directory):

1. **Resolve path**
   - If no arg → use default `/mnt/home/pengcheng.yu/0_del`
   - `realpath -m <path>` to resolve symlinks
   - Reject if path empty, contains shell-meta unhandled by quoting, or is `.` / `..`

2. **Permission + safety check** (run `precheck.sh <path>`)
   - Path must exist and be a directory
   - Path must be owned by `$USER` (the cluster user invoking the skill)
   - Path must be **strictly under** `/mnt/home/<user>/` or `/mnt/data/` and NOT one of the protected roots
   - Protected blacklist (refuse outright):
     `/`, `/mnt`, `/mnt/data`, `/mnt/home`, `$HOME`, `/tmp`, `/var`, `/etc`, `/usr`, `/opt`, `/opt/conda`, `/mnt/data/models`, `/mnt/data/scene4d`, `/mnt/data/pyu`
   - Path under `/mnt/data/` requires `--allow-shared` flag (extra friction, since shared storage)
   - User must have write permission on parent (so we can rmdir if `--remove-root`)

3. **Target summary** (run `du -sh <path>` and `find <path> | wc -l` in parallel via background)
   - Total size (human-readable)
   - File + dir count
   - Top-3 largest immediate subdirs (`du -sh <path>/* 2>/dev/null | sort -rh | head -3`)

4. **Generate `.sbatch`** in `~/0_pyu/pyu-delete/runs/<timestamp>/job.sbatch`
   - Use `template.sbatch` as base; substitute `{{TARGET}}`, `{{PARTITION}}`, `{{NODES}}`, `{{NTASKS}}`, `{{TIME}}`, `{{REMOVE_ROOT}}`, `{{LOGDIR}}`
   - Job name: `pyu-del-<basename>`
   - stdout/stderr in same `runs/<ts>/` dir

5. **Show user**:
   - Resolved target path
   - Summary (size / count / top-3 subdirs)
   - Full `.sbatch` content
   - Prompt: `Type "yes" to submit, anything else to abort.`

6. **On `yes`**: `sbatch <path-to-sbatch>` → report job id + log paths + `squeue -j <id>` follow-up command. **On anything else**: leave the .sbatch on disk for review, do nothing.

7. **After submit**: do NOT poll. Tell user job id, log paths, and the cancel command (`scancel <id>`).

## How the Parallel Worker Splits Work (v2)

`delete_worker.sh` runs via `srun` with `$SLURM_NTASKS` ranks. Pipeline:

1. **Adaptive-depth manifest (rank 0)**:
   Probes `depth=2 → 3 → 4 → ... → 6` until manifest has at least `8×NTASKS`
   work units (e.g. 1024 entries for 128 ranks). Manifest contains:
   - All entries (dir or file) at exactly the chosen `TARGET_DEPTH`
   - All **files** at shallower depths (so root-level loose files still get deleted)
   - **No directories at shallower depth** — they would race with their deeper
     descendants in the manifest. Empty parents are cleaned up in phase-3.

   Other ranks block on `manifest.ready` barrier file.

2. **Start-line barrier (all ranks)**:
   Each rank touches `start.<rank>` then polls until `start.* count == NTASKS`.
   This prevents the manifest-builder rank from draining the work counter while
   other ranks are still waking up. Symmetric (rank 0 also waits) — skew ≤ 100ms.

3. **Work-stealing via flock-protected counter (all ranks)**:
   Counter file holds next-unclaimed-index. Each rank pops `CHUNK_SIZE=4`
   entries atomically via `flock` and `rm -rf`s them. This balances workload
   when a few entries (e.g. one huge benchmark dir) are 1000× larger than
   others — slow ranks naturally claim fewer chunks while fast ranks keep
   popping. flock contention is brief (μs-scale per pop).

4. **Phase-2 done barrier (rank 0)**:
   Each rank touches `done.<rank>` after work loop. Rank 0 polls until all
   `done.*` files exist before phase-3 mop-up. **No more `sleep 5`** — rank 0
   waits for actual completion of every rank.

5. **Phase-3 mop-up (rank 0 only)**:
   `rm -rf $TARGET/*` removes any residual depth-1 entries (empty dirs whose
   contents were processed at deeper levels). If `--remove-root`, then
   `rmdir $TARGET`.

### Why this is faster than v1

| Issue (v1) | Fix (v2) |
|---|---|
| Manifest depth-1+depth-2 → parent/child race left empty skeletons | Adaptive-depth manifest uses **only** leaf-like entries |
| Static round-robin → unbalanced when sizes differ 1000× | **Work-stealing** queue claims next chunk atomically |
| Small `MAX_DEPTH=2` → 13M files in 115 work units (5-13 effective parallel) | Adaptive depth grows until ≥ 8×NTASKS units |
| Phase-3 used `sleep 5` (race with slow ranks) | **File barrier** waits for actual `done.<rank>` count |
| Manifest builder started consuming before peers woke | **Start-line barrier** synchronizes all ranks |

## Files in This Skill

- `SKILL.md` — this file
- `precheck.sh` — standalone safety check; exits non-zero on violation, prints reason
- `delete_worker.sh` — per-rank deletion logic; reads `$MANIFEST`, `$SLURM_PROCID`, `$SLURM_NTASKS`
- `template.sbatch` — sbatch template with `{{PLACEHOLDER}}` substitutions

## Example: full invocation

```
User: /pyu-delete /mnt/home/pengcheng.yu/scratch/old_kubric_dump

Claude:
  → realpath: /mnt/home/pengcheng.yu/scratch/old_kubric_dump
  → precheck.sh: PASS (owner=pengcheng.yu, under $HOME, not blacklisted)
  → summary: 412G, 3,841,022 files; top: 0001/(180G) 0002/(120G) 0003/(90G)
  → wrote sbatch: /mnt/home/pengcheng.yu/0_pyu/pyu-delete/runs/20260507-033012/job.sbatch
  → [show full sbatch content]
  → Type "yes" to submit:

User: yes

Claude:
  → sbatch ... → Submitted batch job 1234567
  → logs: /mnt/home/pengcheng.yu/0_pyu/pyu-delete/runs/20260507-033012/job.{out,err}
  → cancel: scancel 1234567
  → progress: squeue -j 1234567
```

## Notes

- This skill **never** runs `rm -rf` on the login node — always goes through `sbatch`.
- Logs go to `~/0_pyu/pyu-delete/runs/<timestamp>/` — kept after job ends for audit.
- If user wants to cancel during job: `scancel <id>` — partial deletion is safe (already-deleted entries stay deleted; nothing to undo).
- For paths under `/mnt/data/` (shared), require explicit `--allow-shared` flag and double-confirm.
