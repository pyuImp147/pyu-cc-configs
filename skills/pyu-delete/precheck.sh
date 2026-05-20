#!/usr/bin/env bash
# precheck.sh — safety + permission check for pyu-delete
# Usage: precheck.sh <target-path> [--allow-shared]
# Exits 0 if safe to delete; non-zero with reason on stderr otherwise.

set -u

TARGET="${1:-}"
ALLOW_SHARED="${2:-}"

die() { echo "[precheck] REJECT: $*" >&2; exit 2; }

[[ -n "$TARGET" ]] || die "no target path given"

# Resolve symlinks; -m allows non-existent components but we'll check existence below
REAL=$(realpath -m "$TARGET" 2>/dev/null) || die "cannot resolve path: $TARGET"

# Strip any trailing slash for stable comparison
REAL="${REAL%/}"
[[ -n "$REAL" ]] || die "resolved path is empty"

# Existence + type
[[ -e "$REAL" ]] || die "path does not exist: $REAL"
[[ -d "$REAL" ]] || die "path is not a directory: $REAL (refusing to delete a single file via this skill)"

# Owner check — must match invoking user
OWNER=$(stat -c '%U' "$REAL" 2>/dev/null) || die "stat failed on $REAL"
[[ "$OWNER" == "$USER" ]] || die "owner=$OWNER, but USER=$USER. Refusing to delete files you don't own."

# Hard blacklist — exact match (after realpath)
BLACKLIST=(
    "/"
    "/mnt"
    "/mnt/data"
    "/mnt/home"
    "$HOME"
    "/tmp"
    "/var"
    "/etc"
    "/usr"
    "/opt"
    "/opt/conda"
    "/mnt/data/models"
    "/mnt/data/models/huggingface"
    "/mnt/data/scene4d"
    "/mnt/data/pyu"
    "/mnt/data/wheels"
)
for bl in "${BLACKLIST[@]}"; do
    [[ "$REAL" == "$bl" ]] && die "path is in protected blacklist: $REAL"
done

# Must live under one of the allowed roots
ALLOWED_HOME="/mnt/home/$USER"
ALLOWED_DATA="/mnt/data"

UNDER_HOME=0
UNDER_DATA=0
case "$REAL/" in
    "$ALLOWED_HOME"/*) UNDER_HOME=1 ;;
    "$ALLOWED_DATA"/*) UNDER_DATA=1 ;;
esac

if (( UNDER_HOME == 0 && UNDER_DATA == 0 )); then
    die "path not under $ALLOWED_HOME or $ALLOWED_DATA: $REAL"
fi

if (( UNDER_DATA == 1 )) && [[ "$ALLOW_SHARED" != "--allow-shared" ]]; then
    die "path is under shared /mnt/data — pass --allow-shared to confirm intent: $REAL"
fi

# Also reject if too shallow under /mnt/home/<user> (i.e. exactly $HOME)
[[ "$REAL" == "$ALLOWED_HOME" ]] && die "path equals \$HOME — refusing to wipe entire home"

# Parent must be writable (so we can rmdir target if --remove-root is requested later)
PARENT=$(dirname "$REAL")
[[ -w "$PARENT" ]] || die "parent dir not writable by $USER: $PARENT"

# Target itself writable (need write+execute to delete entries inside)
[[ -w "$REAL" && -x "$REAL" ]] || die "target not writable+executable by $USER: $REAL"

echo "[precheck] OK: $REAL (owner=$OWNER, under_home=$UNDER_HOME, under_data=$UNDER_DATA)"
exit 0
