---
name: pyu-traj-vis
description: >-
  Generic viser viewer for 3D pointmap + per-pixel trajectory visualization.
  Source-agnostic — caller supplies (N, T, 3) per-pixel world positions and
  optionally per-frame pointmaps + RGB images; skill produces a viser script
  with full GUI (frame slider, stride, prev/next/reset, accumulate dual-mode,
  per-category visibility, display subsample, point size, image panel) and a
  public viser.studio share-link by default.
  TRIGGER when: user wants to visualize 3D point trajectories or pointmap with
  viser, or asks for "show me how (u,v,t_src,t_tgt)→p_world looks" style query
  visualization across any dataset (MetaHuman / SynthVerse / PhysInOne /
  PointOdyssey / Kubric / DynamicReplica / custom).
  DO NOT TRIGGER when: user wants 2D-only visualization, matplotlib plots,
  static screenshot dumps, or asks how to COMPUTE the trajectories (this skill
  only renders, it doesn't derive p_world from sources).
origin: pyu-personal
---

# pyu-traj-vis — Generic 3D Pointmap + Trajectory Viser Viewer

Render any dataset's `(N, T, 3)` per-pixel world trajectories + per-frame pointmaps as an interactive viser scene with a public share-link. Visualization is **dataset-agnostic** — pipeline that produces the trajectories (e.g. MetaHuman unproject+barycentric, SynthVerse direct annotation, Kubric per-frame XYZ, custom) is completely outside this skill's scope.

## When to Use

- User has computed trajectories `(N, T, 3) world meters` and wants a 3D viewer
- User wants to inspect 5-元 query (`u, v, t_src, t_tgt, t_cam`) → `p_world(t_tgt)` style results
- User wants 2D image overlay synced with 3D pointmap (e.g. show "this pixel here, traced to that 3D point at t_tgt")
- User asks for "viser viewer with dense pointmap + sparse trajectory" pattern

## When NOT to Use

- Trajectory data is in 2D image space only (use matplotlib / cv2)
- User wants Python-only inspection without a 3D server (use `np.savez` + offline plotting)
- User wants the *pipeline* that produces world trajectories (out of scope; e.g. for MetaHuman see `data-explore/scripts/viser_metahuman_pointmap_trajectory.py` for an integrated reference example)

## How It Works

The skill ships:
1. `traj_viewer.py` — reusable Python module exposing `launch_traj_viewer(...)`.
2. `examples/demo_synthetic.py` — fully runnable synthetic example (no external data needed).

When invoked, Claude should:
1. **Interview the user** for these inputs:
   - **Source** (where does trajectory data come from? — npz file path / Python expression / function callback)
   - **Pixel selection** (which `(u, v)` indices? — full grid, subsample stride, mask file, list of explicit points?)
   - **Frame range** (`t_src`, `t_tgt` window — single source frame or sweep all?)
   - **Categories** (one bucket or multiple, e.g. moving vs static, MH vs non-MH?)
   - **Optional auxiliaries** (per-frame pointmap loader? per-frame RGB images? camera pose for frustum?)
2. **Generate a thin script** that:
   - Loads / computes the user's trajectory arrays
   - Calls `launch_traj_viewer(trajectories=..., T=..., share=True, port=8893, ...)`
3. **Save the script** to a sensible path (default `0_debug/<topic>/viewer.py` or wherever the user prefers — never inside this skill's dir).
4. **Run the script** in background with `--share` and surface the public URL.

## API Contract — `launch_traj_viewer(...)`

```python
from traj_viewer import launch_traj_viewer

launch_traj_viewer(
    # ── Required ─────────────────────────────────────────────────────────────
    trajectories: dict[str, dict],
    # category_name -> {
    #     'world_pos': (N, T, 3) float32,   # per-pixel world position over time
    #     'uvs':       (N, 2) int   | None, # source pixel coords (for 2D overlay)
    #     'colors':    (N, 3) uint8 | None, # per-uv base hue; auto-derived if None
    # }
    T: int,                                  # number of frames

    # ── Optional: per-frame dense pointmap ───────────────────────────────────
    pointmap_loader: Callable[[int], tuple[np.ndarray, np.ndarray]] | None = None,
    # frame_idx -> (pts (M, 3) float32, colors (M, 3) uint8)

    # ── Optional: per-frame RGB images (for image panel) ─────────────────────
    image_loader: Callable[[int], np.ndarray] | None = None,
    # frame_idx -> (H, W, 3) uint8

    # ── Optional: camera frustum (clickable teleport) ────────────────────────
    # Pose: (4, 4) static  OR  (T, 4, 4) per-frame OpenCV cam-to-world.
    # Intrinsics: dict {fx, fy, cx, cy, w, h} static  OR  list[dict] length T per-frame.
    # When per-frame is given, the frustum (pose, fov, aspect, image) re-renders
    # on every frame slider update — i.e. it tracks current = t_tgt.
    camera_pose_c2w: np.ndarray | None = None,
    camera_intrinsics: dict | list[dict] | None = None,

    # ── Scene + server ───────────────────────────────────────────────────────
    t_src: int = 0,
    scene_focus: np.ndarray | None = None,   # auto from trajectories if None
    up: str = "-y",                          # "-y" OpenCV / "+y" OpenGL / "+z" Blender
    port: int = 8893,
    share: bool = True,                      # request public viser.studio tunnel
    title: str = "Trajectory Viewer",
)
```

## Color Encoding (defaults)

- **Per-uv hue**: 2D HSV `hue=(u/W + 1.7·v/H) mod 1`, sat=0.95, value 0.65→1.0 over v
- **Per-t opacity**: linear 0.2 → 1.0 from t_src to T-1 (later = brighter)
- Override by supplying `colors` in trajectories dict

## GUI Layout (top → bottom)

The viewer renders GUI elements in this order so the most-used controls (frame navigation + image preview) sit together at the top, with toggles and per-frame tuning sliders pushed below:

**1. Frame controls (top)**

| Control | Effect |
|---|---|
| `Frame (t_tgt)` slider | 0..T-1 — current target frame |
| `Frame Stride` slider | 1..T — Next/Prev / Play jump size |
| `◀ Prev Frame` / `Next Frame ▶` buttons | step by stride |
| `▶ Play (auto-step)` checkbox | run a daemon thread that advances frame by stride; auto-stops at last frame |
| `Play FPS` slider | 1..60 — speed of auto-step |
| `⟲ Reset` button | restore all GUI defaults + camera to scene_focus |

**2. Image Panel** (folder, immediately below frame controls — `image_loader` required)

| Control | Effect |
|---|---|
| `t_src=N (annotated)` image | source-frame RGB with per-uv-colored dots at every subsampled track (synced to 3D hue) |
| `t_tgt (current)` image | RGB at current frame, updates with frame slider |

**3. Visibility checkboxes**

| Control | Effect |
|---|---|
| `Pointmap (current frame)` checkbox | toggles **only** the current-frame pointmap (and the stride-aligned history when accumulate is ON). Does NOT affect the t_src pointmap. |
| `Always Show t_src Pointmap` checkbox | default **True** — independently toggles the t_src frame pointmap. Combine with `Pointmap (current frame)`: e.g. show only t_src by turning current OFF, anchor ON. |
| `Re-color t_src (dark blue)` checkbox | default **True** — when both t_src and current pointmaps are on, the t_src cloud is tinted with a heavy blue blend (`c' = 0.35·c + 0.65·blue`, blue=`(0, 51, 217)`) so it's clearly separable from the current-frame cloud at any zoom level. Tinting is computed once per pointmap and stored; toggling just swaps the colors array. |
| `Accumulate Pointmap History` checkbox | OFF → only the cur + (anchored) t_src frames render; ON → adds stride-aligned intermediate frames as dim history (only when `Pointmap (current frame)` is ON) |
| `Show Camera Frustum` checkbox | toggle camera frustum + frame-node visibility (in per-frame mode this toggles all history frustums) |
| `Pairwise Traj Vis` checkbox | **OFF** (default) = growing-history polylines `[0..cur]` (slider-driven); **ON** = 1 straight segment per query from `t_src → t_tgt` (no intermediate samples). Both modes play-compatible. |
| `Tracks: <category>` checkboxes | per-category visibility (one per trajectory dict key) |

**4. Tuning sliders (bottom)**

| Control | Effect |
|---|---|
| `Display Subsample (stride)` | render every k-th trajectory + 2D dot; default 8 |
| `Point size` slider | 0.001..0.05 m for pointmap |
| `Track Line Width` slider | 0.1..2.5 for trajectory polylines; default 1.0 |

**Misc**

- Camera frustum (if `camera_pose_c2w` + `camera_intrinsics` given): every frustum is clickable → teleport viewer to that pose; visibility controlled by `Show Camera Frustum` checkbox.
  - **Static mode** (`(4, 4)` + dict): one frustum fixed at `t_src` pose, with t_src RGB on the frustum image.
  - **Per-frame mode** (`(T, 4, 4)` + `list[dict]`): renders the **full camera trajectory up to current = t_tgt** — one frustum per frame in `[0..cur]`. Current frustum is **blue + current RGB image**, the `t_src` anchor frustum is **green + t_src RGB**, all other history frustums are **gray (no image)**. This makes a long sequence (e.g. PointOdyssey 1500 frames) trace out the actual camera path through the scene.
- All handlers refresh on slider/checkbox change (no need to click "apply")
- **Play loop**: daemon thread tied to `gui_play` + `gui_fps`. Stops on `KeyboardInterrupt` (skill exit) or at last frame (sets `gui_play.value = False`).

## Example — Synthetic (no real dataset needed)

See `examples/demo_synthetic.py`:
```bash
python -m skill_pyu_traj_vis.examples.demo_synthetic --share
# or copy traj_viewer.py + the demo into the user's repo and run
```

Generates 2 categories of synthetic 3D motion (helix + static dot grid), 30 frames, full GUI + share-link.

## Concrete reference example (real dataset)

For a real MetaHuman pipeline integration that *uses* this viewer pattern (with unproject+barycentric upstream), see `data-explore/scripts/viser_metahuman_pointmap_trajectory.py` in the calling repo. That script is the one this skill was distilled from — it's NOT part of this skill but serves as a reference of the upstream-pipeline shape.

## Workflow Checklist

When generating a viewer for the user:

- [ ] Confirm trajectory shape `(N, T, 3) float32` world meters
- [ ] Confirm `T` and pixel selection (full grid? mask? explicit list?)
- [ ] Confirm coordinate convention (`up = "-y" | "+y" | "+z"`)
- [ ] Decide categories (1 or many? what's the visual split?)
- [ ] Decide auxiliaries (pointmap? images? cam frustum?)
- [ ] If `uvs` were captured at a different resolution than the rendered RGB / pointmap, **rescale them before passing** (e.g. result.npz video is post-resize but query_uvs captured pre-resize → scale by `(W_out/W_in, H_out/H_in)`)
- [ ] Generate caller script — keep < 100 lines, all the heavy lifting in `traj_viewer.launch_traj_viewer`
- [ ] Run in background, return share-link
- [ ] Tell user how to kill the server (⚠ **NOT** `pkill -f <viewer.py>` — if your kill command itself contains that pattern, pkill will match the parent bash and self-kill with exit 144). Use `ps -eo pid,cmd | grep -v grep | grep '<viewer.py>' | awk '{print $1}' | xargs -r kill` instead.

## Files Shipped

- `SKILL.md` — this file
- `traj_viewer.py` — the reusable viewer module
- `examples/demo_synthetic.py` — runnable synthetic example
