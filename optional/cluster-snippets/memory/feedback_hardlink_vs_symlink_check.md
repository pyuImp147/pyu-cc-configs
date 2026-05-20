---
name: feedback-hardlink-vs-symlink-check
description: "Never use `ls -i` alone to identify hard links — use `ls -la` to see file type ('l' vs '-'). Mistaking symlink for hardlink can cause real data deletion."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ac6f4db-1a12-4b5c-a456-dce3451f4b24
---

判断两个 path 是否是 hard link（删一个不影响另一个）**绝对不能**只看 `ls -i` 的 inode 是否一致。

**Why**: `ls -i` 默认 follow symlink → symlink 在 resolve 后会返回 target 的 inode，所以"两侧 inode 一致"对 hard link 和 symlink **都成立**。2026-05-18 一次事故中我用 `ls -i` 看到 `/mnt/data/scene4d/d4rt/kubric/raw/movi_f/512x512/...` 和 `/mnt/data/scene4d/d4rt/kubric/raw/512x512/...` inode 一致，断言是 hard link，建议 user 删除 `raw/512x512`。实际 `raw/movi_f/512x512 -> ../512x512` 是 symlink，删 target 等于真删 552G NFS 数据，且 NFS 无 trash。

**How to apply**:
- 涉及 `rm` 前，判断 path 关系时**总用** `ls -la <path>` 看 file type 字符（`-` = regular file/dir, `l` = symlink, hard link 之间也是 `-`）。
- 想确认 hard link：`stat -c "%h" <path>` 看 link count > 1，并用 `find <dir> -inum <ino>` 找出所有 hard-link path；或 `ls -li` 配合**对 directory entry 自身**（不是 follow target）看。
- 想确认 symlink：`readlink <path>` 或 `ls -la <parent>` 直接看箭头 `-> target`。
- `du -sh` 对 symlink 显示 4 字节（symlink 本身大小），对 hard link 重复 path 显示 0 —— 看到 "两个 path 一个有 size 一个 0" 不要直接断 hard link，先 `ls -la`。
- 涉及共享存储（NFS / PVC）的删除：除非已用 `ls -la` 直接看出 file type，否则**永不**确认。NFS 通常没 trash / undelete。
