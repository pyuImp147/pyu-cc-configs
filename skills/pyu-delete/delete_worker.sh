#!/usr/bin/env bash
# delete_worker.sh v2 — per-rank deletion worker (work-stealing + adaptive depth)
#
# Fixes vs v1:
#   1. Adaptive depth: walk deeper than maxdepth=2 until we have ≥ 8×NTASKS
#      work units, so 128 ranks aren't bottlenecked by 5-13 huge top-level dirs.
#   2. Leaf-only manifest: items at exactly TARGET_DEPTH (any type) + files at
#      shallower depths. NEVER both a parent dir and its descendants — eliminates
#      the depth-1 vs depth-2 race that left empty skeletons in v1.
#   3. Work-stealing queue: ranks pop chunks from a shared counter via flock.
#      Beats static round-robin when a few work units are 1000× larger than
#      others (typical for ML datasets).
#   4. Real barrier: each rank touches done.<rank> after phase-2; rank 0 polls
#      until all NTASKS done-files exist before phase-3 mop-up. No more sleep 5.
#
# Env in: TARGET, MANIFEST (path), REMOVE_ROOT (0|1)
# Env from SLURM: SLURM_PROCID, SLURM_NTASKS, SLURMD_NODENAME

set -u

TARGET="${TARGET:?TARGET env not set}"
MANIFEST="${MANIFEST:?MANIFEST env not set}"
REMOVE_ROOT="${REMOVE_ROOT:-0}"

RANK="${SLURM_PROCID:-0}"
NTASKS="${SLURM_NTASKS:-1}"
NODE="${SLURMD_NODENAME:-$(hostname)}"

LOGDIR=$(dirname "$MANIFEST")
BARRIER_READY="${MANIFEST}.ready"
COUNTER_FILE="${MANIFEST}.counter"
COUNTER_LOCK="${MANIFEST}.counter.lock"
DONE_DIR="${LOGDIR}/done"

CHUNK_SIZE=4        # how many entries each rank claims per flock — small to keep ranks balanced
MIN_UNITS_FACTOR=8  # target manifest size = MIN_UNITS_FACTOR * NTASKS
MAX_DEPTH_LIMIT=6   # don't go deeper than this (to avoid pathological enumeration)

log() { echo "[r=$RANK n=$NODE] $*"; }

# ── Phase 1: rank 0 builds adaptive-depth manifest ──────────────────────────
if (( RANK == 0 )); then
    mkdir -p "$DONE_DIR"
    : > "$MANIFEST"
    echo 0 > "$COUNTER_FILE"

    MIN_UNITS=$(( MIN_UNITS_FACTOR * NTASKS ))
    log "target ≥ $MIN_UNITS work units; probing depth..."

    DEPTH=2
    while (( DEPTH <= MAX_DEPTH_LIMIT )); do
        # entries at exactly DEPTH (any type) + files at shallower depths
        # (we don't include shallower DIRECTORIES — those would race with
        #  their deeper descendants in the manifest)
        {
            find "$TARGET" -mindepth "$DEPTH" -maxdepth "$DEPTH" 2>/dev/null
            if (( DEPTH > 1 )); then
                find "$TARGET" -mindepth 1 -maxdepth $((DEPTH - 1)) -type f 2>/dev/null
            fi
        } > "${MANIFEST}.tmp"

        COUNT=$(wc -l < "${MANIFEST}.tmp")
        log "  depth=$DEPTH → $COUNT entries"

        if (( COUNT >= MIN_UNITS )); then
            mv "${MANIFEST}.tmp" "$MANIFEST"
            log "manifest finalized at depth=$DEPTH with $COUNT entries"
            break
        fi

        # If even depth=MAX_DEPTH_LIMIT can't reach MIN_UNITS, accept it
        if (( DEPTH == MAX_DEPTH_LIMIT )); then
            mv "${MANIFEST}.tmp" "$MANIFEST"
            log "manifest finalized at MAX depth=$DEPTH with $COUNT entries (under target, but stopping)"
            break
        fi

        # Discard insufficient manifest, try deeper
        rm -f "${MANIFEST}.tmp"
        DEPTH=$((DEPTH + 1))
    done

    # Defensive: if manifest somehow ended up empty, salvage with depth-1 entries
    if [[ ! -s "$MANIFEST" ]]; then
        log "WARN: manifest empty, falling back to depth-1 entries"
        find "$TARGET" -mindepth 1 -maxdepth 1 > "$MANIFEST"
    fi

    TOTAL_LINES=$(wc -l < "$MANIFEST")
    log "MANIFEST_TOTAL=$TOTAL_LINES"
    touch "$BARRIER_READY"
else
    log "waiting for manifest..."
    timeout 1800 bash -c "until [[ -f '$BARRIER_READY' ]]; do sleep 2; done" \
        || { log "ERROR: manifest barrier wait timed out (30 min)"; exit 3; }
fi

TOTAL_LINES=$(wc -l < "$MANIFEST")

# ── Start-line barrier: ALL ranks (including rank 0) must arrive before ANY
# starts popping work. Otherwise the rank that built the manifest drains the
# counter before slower ranks wake from polling. Symmetric wait keeps skew
# below ~100ms.
mkdir -p "$DONE_DIR"
touch "${DONE_DIR}/start.${RANK}"
timeout 1800 bash -c "
    while :; do
        n=\$(find '$DONE_DIR' -maxdepth 1 -name 'start.*' 2>/dev/null | wc -l)
        if (( n >= $NTASKS )); then break; fi
        sleep 0.1
    done
" || { log "ERROR: start-line barrier timed out"; exit 5; }

log "starting work-stealing pop loop (TOTAL=$TOTAL_LINES, chunk=$CHUNK_SIZE)"

# ── Phase 2: dynamic work-stealing via flock-protected counter ──────────────
DELETED=0
FAILED=0
SKIPPED=0

# Pop next chunk: returns "start_idx end_idx" (inclusive..exclusive)
pop_chunk() {
    flock -x 200
    local idx
    idx=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
    echo $((idx + CHUNK_SIZE)) > "$COUNTER_FILE"
    echo "$idx"
}

while :; do
    START=$(exec 200>"$COUNTER_LOCK"; pop_chunk)
    END=$((START + CHUNK_SIZE))
    if (( START >= TOTAL_LINES )); then
        break
    fi
    if (( END > TOTAL_LINES )); then
        END=$TOTAL_LINES
    fi

    # Read lines [START+1 .. END] from manifest (1-indexed)
    mapfile -t CHUNK < <(awk -v s=$((START + 1)) -v e=$END 'NR >= s && NR <= e' "$MANIFEST")

    for entry in "${CHUNK[@]}"; do
        [[ -z "$entry" ]] && continue
        # Defense: never delete outside TARGET
        case "$entry/" in
            "$TARGET"/*) : ;;
            *) log "SKIP (outside target): $entry"; SKIPPED=$((SKIPPED + 1)); continue ;;
        esac

        if [[ ! -e "$entry" ]]; then
            # already gone (sibling rank claimed parent — shouldn't happen with leaf-only
            # manifest, but defensive)
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        if rm -rf -- "$entry" 2>/dev/null; then
            DELETED=$((DELETED + 1))
        else
            FAILED=$((FAILED + 1))
            log "FAILED: $entry"
        fi
    done
done

log "phase-2 done: deleted=$DELETED failed=$FAILED skipped=$SKIPPED"

# ── Barrier: signal phase-2 done, wait for all ranks ────────────────────────
touch "${DONE_DIR}/done.${RANK}"

if (( RANK == 0 )); then
    log "waiting for all $NTASKS ranks to finish phase-2..."
    timeout 14400 bash -c "
        while :; do
            n=\$(find '$DONE_DIR' -maxdepth 1 -name 'done.*' | wc -l)
            if (( n >= $NTASKS )); then break; fi
            sleep 5
        done
    " || { log "ERROR: phase-2 barrier wait timed out (4h)"; exit 4; }
    log "all $NTASKS ranks done with phase-2"

    # ── Phase 3: mop-up residual depth-1 entries ────────────────────────────
    log "phase-3 mop-up under $TARGET"
    shopt -s dotglob nullglob
    leftovers=( "$TARGET"/* )
    shopt -u dotglob nullglob
    if (( ${#leftovers[@]} > 0 )); then
        log "found ${#leftovers[@]} leftover entries, removing"
        for lo in "${leftovers[@]}"; do
            rm -rf -- "$lo" 2>/dev/null || log "WARN: could not remove $lo"
        done
        # Final check
        shopt -s dotglob nullglob
        still=( "$TARGET"/* )
        shopt -u dotglob nullglob
        if (( ${#still[@]} > 0 )); then
            log "WARN: ${#still[@]} entries still remain after mop-up:"
            printf '   %s\n' "${still[@]:0:20}"
        else
            log "mop-up clean: 0 leftovers"
        fi
    else
        log "no leftovers"
    fi

    if [[ "$REMOVE_ROOT" == "1" ]]; then
        log "removing root dir: $TARGET"
        rmdir -- "$TARGET" 2>/dev/null || log "WARN: rmdir root failed (likely not empty)"
    else
        log "preserving root dir: $TARGET"
    fi

    # Clean up state files (keep job.out / job.err in LOGDIR for audit)
    rm -f "$BARRIER_READY" "$MANIFEST" "$COUNTER_FILE" "$COUNTER_LOCK"
    rm -rf "$DONE_DIR"

    log "ALL DONE"
fi

exit 0
