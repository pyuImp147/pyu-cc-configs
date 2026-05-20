#!/bin/bash
#SBATCH --job-name={{JOBNAME}}
#SBATCH --partition={{PARTITION}}
#SBATCH --nodes={{NODES}}
#SBATCH --ntasks-per-node={{NTASKS_PER_NODE}}
#SBATCH --cpus-per-task={{CPUS_PER_TASK}}
#SBATCH --mem={{MEM}}
#SBATCH --time={{TIME}}
#SBATCH --output={{LOGDIR}}/job.out
#SBATCH --error={{LOGDIR}}/job.err

# pyu-delete sbatch — generated {{TIMESTAMP}}
# Target : {{TARGET}}
# Worker : {{WORKER}}
# Nodes  : {{NODES}}  Tasks/node: {{NTASKS_PER_NODE}}  Total ranks: {{TOTAL_RANKS}}
# RemoveRoot: {{REMOVE_ROOT}}

set -euo pipefail

echo "=== pyu-delete START $(date -Is) ==="
echo "  TARGET     = {{TARGET}}"
echo "  PARTITION  = {{PARTITION}}"
echo "  NODES      = {{NODES}}"
echo "  NTASKS     = $SLURM_NTASKS"
echo "  JOBID      = $SLURM_JOB_ID"
echo "  LOGDIR     = {{LOGDIR}}"
echo "  REMOVE_ROOT= {{REMOVE_ROOT}}"
echo

# Re-run precheck inside the job — defends against target being moved/changed
# between client-side check and job start.
PRECHECK="{{PRECHECK}}"
if ! bash "$PRECHECK" "{{TARGET}}" {{ALLOW_SHARED_FLAG}}; then
    echo "FATAL: precheck failed inside sbatch job — aborting"
    exit 4
fi

export TARGET="{{TARGET}}"
export MANIFEST="{{LOGDIR}}/manifest.txt"
export REMOVE_ROOT="{{REMOVE_ROOT}}"
WORKER="{{WORKER}}"

# srun runs the worker on every rank across all allocated nodes.
# --kill-on-bad-exit so one rank failing doesn't leave others hanging.
srun --kill-on-bad-exit=1 bash "$WORKER"

echo "=== pyu-delete END $(date -Is) ==="

# Final sanity: print remaining size if target still exists
if [[ -d "{{TARGET}}" ]]; then
    echo "Target dir still exists. Remaining contents:"
    ls -la "{{TARGET}}" | head -20
    REMAIN=$(du -sh "{{TARGET}}" 2>/dev/null | cut -f1)
    echo "Remaining size: $REMAIN"
else
    echo "Target dir removed cleanly."
fi
