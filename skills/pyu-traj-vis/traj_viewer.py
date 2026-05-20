"""Reusable viser viewer for 3D pointmap + per-pixel trajectory visualization.

Source-agnostic — caller supplies (N, T, 3) world trajectories and optional
per-frame pointmap / image loaders. The viewer renders:

  - dense pointmap (lazy, per-frame) with bright/dim accumulation modes
  - per-pixel trajectory polylines, hue=per-uv, opacity=per-t
  - GUI (frame slider, stride, prev/next/reset, accumulate dual-mode,
    per-category visibility, display subsample, point size)
  - 2D image panel (t_src annotated + t_tgt current) — if image_loader given
  - clickable camera frustum that teleports the viewer

See SKILL.md for the API contract and usage.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

import numpy as np


# ── Color helpers ────────────────────────────────────────────────────────────


def per_uv_base_colors(uvs: np.ndarray, W: int, H: int) -> np.ndarray:
    """Map (u, v) → unique HSV base color. Diagonal hue + value gradient.

    Args:
        uvs: (N, 2) int, columns = (u, v).
        W, H: image width / height for normalization.

    Returns: (N, 3) uint8 RGB.
    """
    from matplotlib.colors import hsv_to_rgb

    if len(uvs) == 0:
        return np.zeros((0, 3), dtype=np.uint8)
    u_n = uvs[:, 0].astype(np.float32) / max(W - 1, 1)
    v_n = uvs[:, 1].astype(np.float32) / max(H - 1, 1)
    hsv = np.stack(
        [
            (u_n + 1.7 * v_n) % 1.0,
            np.full(len(uvs), 0.95, dtype=np.float32),
            0.65 + 0.35 * (1.0 - v_n),
        ],
        axis=-1,
    )
    rgb = hsv_to_rgb(hsv)
    return (rgb * 255).clip(0, 255).astype(np.uint8)


def fallback_index_colors(N: int, seed: int = 42) -> np.ndarray:
    """Deterministic per-index colors when no (u, v) is available."""
    rng = np.random.default_rng(seed)
    return rng.integers(80, 256, size=(N, 3), dtype=np.uint8)


def build_segments_per_pixel(
    world_pos: np.ndarray, base_colors: np.ndarray, cur_t: int
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """world_pos: (N, T, 3); base_colors: (N, 3) uint8; cur_t: int 0..T-1.

    Returns (M, 2, 3) points + (M, 2, 3) uint8 colors for segments [t, t+1]
    where t < cur_t. None if no segments.
    """
    if cur_t < 1 or world_pos.shape[0] == 0:
        return None, None
    N, T, _ = world_pos.shape
    seg_t = np.arange(cur_t)
    starts = world_pos[:, seg_t]
    ends = world_pos[:, seg_t + 1]
    pts = np.stack([starts, ends], axis=2).reshape(-1, 2, 3).astype(np.float32)
    alphas = np.linspace(0.2, 1.0, max(T - 1, 1), dtype=np.float32)
    alpha_seg = alphas[seg_t]
    cols_nt = (
        base_colors[:, None, :].astype(np.float32) * alpha_seg[None, :, None]
    ).clip(0, 255).astype(np.uint8)
    cols = np.broadcast_to(cols_nt[:, :, None, :], (N, cur_t, 2, 3)).reshape(-1, 2, 3)
    finite = np.isfinite(pts).all(axis=(1, 2))
    return pts[finite], cols[finite]


def annotate_pixels_on_image(
    rgb_base: np.ndarray,
    cat_uvs: list[tuple[np.ndarray, np.ndarray]],
    stride: int = 8,
    radius: int = 2,
) -> np.ndarray:
    """Draw colored dots on an RGB image. cat_uvs: list of (uvs, colors) per category."""
    import cv2

    out_bgr = cv2.cvtColor(rgb_base, cv2.COLOR_RGB2BGR)
    for uvs, cols in cat_uvs:
        if uvs is None or len(uvs) == 0:
            continue
        for uv, col in zip(uvs[::stride], cols[::stride]):
            cv2.circle(
                out_bgr,
                (int(uv[0]), int(uv[1])),
                radius,
                (int(col[2]), int(col[1]), int(col[0])),  # BGR for cv2
                -1,
            )
    return cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)


# ── Main entry point ─────────────────────────────────────────────────────────


def launch_traj_viewer(
    trajectories: dict[str, dict],
    T: int,
    pointmap_loader: Callable[[int], tuple[np.ndarray, np.ndarray]] | None = None,
    image_loader: Callable[[int], np.ndarray] | None = None,
    overlay_loader: Callable[[int], np.ndarray] | None = None,
    marker_loader: Callable[[int], tuple[np.ndarray, np.ndarray]] | None = None,
    image_size: tuple[int, int] | None = None,
    camera_pose_c2w: np.ndarray | None = None,
    camera_intrinsics: dict | None = None,
    t_src: int = 0,
    scene_focus: np.ndarray | None = None,
    scene_radius: float | None = None,
    up: str = "-y",
    port: int = 8893,
    share: bool = True,
    title: str = "Trajectory Viewer",
    marker_label: str = "Endpoint Markers",
) -> None:
    """Launch the interactive viser server. Blocks until KeyboardInterrupt.

    See SKILL.md for full API contract.
    """
    import viser
    import viser.transforms as vt

    # ── Validate + auto-fill colors ──────────────────────────────────────────
    cat_names = list(trajectories.keys())
    for name, data in trajectories.items():
        wp = np.asarray(data["world_pos"], dtype=np.float32)
        assert wp.ndim == 3 and wp.shape[1] == T and wp.shape[2] == 3, (
            f"trajectories[{name!r}].world_pos must be (N, T={T}, 3); got {wp.shape}"
        )
        data["world_pos"] = wp
        N = wp.shape[0]

        if data.get("colors") is None:
            uvs = data.get("uvs")
            if uvs is not None and image_size is not None:
                W_im, H_im = image_size
                data["colors"] = per_uv_base_colors(np.asarray(uvs), W_im, H_im)
            else:
                data["colors"] = fallback_index_colors(N)
        else:
            data["colors"] = np.asarray(data["colors"], dtype=np.uint8)

        if data.get("uvs") is not None:
            data["uvs"] = np.asarray(data["uvs"], dtype=np.int64)

    # ── Scene focus + radius (used for auto-centering camera on connect) ─────
    # Aggregate t_src points across ALL categories so the camera frames the
    # whole scene, not just one category's median.
    all_t_src_finite = []
    for d in trajectories.values():
        wp = d["world_pos"]
        pts = wp[:, t_src]  # (N_cat, 3)
        finite_mask = np.isfinite(pts).all(axis=1)
        if finite_mask.any():
            all_t_src_finite.append(pts[finite_mask])
    if all_t_src_finite:
        flat = np.concatenate(all_t_src_finite, axis=0)
        if scene_focus is None:
            scene_focus = np.median(flat, axis=0).astype(np.float64)
        if scene_radius is None:
            dists = np.linalg.norm(flat - np.asarray(scene_focus)[None, :], axis=1)
            scene_radius = float(np.median(dists)) * 2.0 if len(dists) else 3.0
    else:
        if scene_focus is None:
            scene_focus = np.zeros(3, dtype=np.float64)
        if scene_radius is None:
            scene_radius = 3.0
    scene_focus = np.asarray(scene_focus, dtype=np.float64)
    scene_radius = float(max(scene_radius, 0.5))

    # Default camera pull-back: opposite of up-axis perpendicular plane.
    # For "-y" (OpenCV) / "+y" (OpenGL) → camera pulls back along -Z.
    # For "+z" / "-z" (Blender / world-Z up) → pulls back along -Y.
    _up_axis = up[-1].lower() if up else "y"
    _back = np.array([0.0, 0.0, -1.0]) if _up_axis == "y" else np.array([0.0, -1.0, 0.0])
    _initial_cam_pos = tuple(scene_focus + _back * 2.0 * scene_radius)

    # ── viser server ─────────────────────────────────────────────────────────
    server = viser.ViserServer(host="0.0.0.0", port=port)
    server.scene.set_up_direction(up)
    if share:
        try:
            url = server.request_share_url()
            print(f"[traj_viewer] PUBLIC SHARE URL: {url}", flush=True)
        except Exception as e:
            print(f"[traj_viewer] share URL request failed: {e}", flush=True)

    # ── GUI ──────────────────────────────────────────────────────────────────
    server.gui.add_markdown(f"## {title}")
    counts_md = " · ".join(
        f"{name}={d['world_pos'].shape[0]}" for name, d in trajectories.items()
    )
    server.gui.add_markdown(f"T={T} · t_src={t_src} · {counts_md}")

    # ── Frame controls (top) ─────────────────────────────────────────────────
    gui_frame = server.gui.add_slider("Frame (t_tgt)", min=0, max=T - 1, step=1, initial_value=t_src)
    gui_stride = server.gui.add_slider("Frame Stride", min=1, max=max(T - 1, 1), step=1, initial_value=1)
    gui_prev = server.gui.add_button("◀ Prev Frame")
    gui_next = server.gui.add_button("Next Frame ▶")
    gui_play = server.gui.add_checkbox("▶ Play (auto-step)", initial_value=False)
    gui_fps = server.gui.add_slider("Play FPS", min=1, max=60, step=1, initial_value=10)
    gui_reset = server.gui.add_button("⟲ Reset")

    # ── Image Panel (immediately below frame controls) ──────────────────────
    src_img_handle = None
    cur_img_handle = None
    overlay_img_handle = None
    rgb_cache: dict = {}

    def _ensure_rgb(frame_idx: int) -> np.ndarray:
        if frame_idx not in rgb_cache:
            rgb_cache[frame_idx] = np.asarray(image_loader(frame_idx))
        return rgb_cache[frame_idx]

    def _annotated_src(stride: int) -> np.ndarray:
        base = _ensure_rgb(t_src).copy()
        cat_uvs = [
            (trajectories[n].get("uvs"), trajectories[n]["colors"]) for n in cat_names
        ]
        return annotate_pixels_on_image(base, cat_uvs, stride=stride)

    if image_loader is not None:
        img_panel = server.gui.add_folder("Image Panel")
        with img_panel:
            src_img_handle = server.gui.add_image(_annotated_src(8), label=f"t_src={t_src} (annotated)")
            cur_img_handle = server.gui.add_image(_ensure_rgb(t_src), label="t_tgt (current)")
            if overlay_loader is not None:
                overlay_img_handle = server.gui.add_image(
                    overlay_loader(t_src), label="t_src + vis overlay (red=occluded)"
                )

    # ── Visibility checkboxes ────────────────────────────────────────────────
    gui_show_pmap = server.gui.add_checkbox("Pointmap (current frame)", initial_value=True)
    gui_anchor_tsrc = server.gui.add_checkbox(
        "Always Show t_src Pointmap", initial_value=True
    )
    gui_recolor_tsrc = server.gui.add_checkbox(
        "Re-color t_src (dark blue)", initial_value=True
    )
    gui_accumulate = server.gui.add_checkbox("Accumulate Pointmap History", initial_value=False)
    gui_show_camera = server.gui.add_checkbox("Show Camera Frustum", initial_value=True)
    gui_show_markers = server.gui.add_checkbox(marker_label, initial_value=True)
    gui_tint_markers = server.gui.add_checkbox(
        "Tint Markers (dark red)", initial_value=False
    )
    gui_partial_traj = server.gui.add_checkbox(
        "Pairwise Traj Vis", initial_value=False
    )
    gui_show_track = {
        name: server.gui.add_checkbox(f"Tracks: {name}", initial_value=True)
        for name in cat_names
    }

    # ── Tuning sliders (bottom) ──────────────────────────────────────────────
    gui_subsample = server.gui.add_slider(
        "Display Subsample (stride)", min=1, max=64, step=1, initial_value=8
    )
    gui_pt_size = server.gui.add_slider(
        "Point size", min=0.001, max=0.05, step=0.001, initial_value=0.005
    )
    gui_line_width = server.gui.add_slider(
        "Track Line Width", min=0.1, max=2.5, step=0.1, initial_value=1.0
    )

    # ── Pointmap (lazy per-frame) ────────────────────────────────────────────
    pcd_handles: dict = {}
    pcd_bright: dict = {}
    pcd_dim: dict = {}
    pcd_tsrc_tint: dict = {}  # only populated for idx == t_src
    HIST_DIM = 0.35
    # st4rtrack-style tint: blend each pixel color with a saturated blue.
    # Heavier blend (lower TSRC_BLEND) + brighter blue → clearer separation
    # from the current-frame pointmap.
    TSRC_TINT_RGB = np.array([0.0, 0.20, 0.85], dtype=np.float32)  # saturated blue
    TSRC_BLEND = 0.35  # higher = more original RGB; lower = more blue

    def _tint_colors(cols_u8: np.ndarray) -> np.ndarray:
        c = cols_u8.astype(np.float32) / 255.0
        c = c * TSRC_BLEND + TSRC_TINT_RGB[None, :] * (1.0 - TSRC_BLEND)
        return (np.clip(c, 0.0, 1.0) * 255.0).astype(np.uint8)

    def _ensure_pcd(idx: int):
        if pointmap_loader is None or idx in pcd_handles:
            return
        pts, cols = pointmap_loader(idx)
        pts = np.asarray(pts, dtype=np.float32)
        cols = np.asarray(cols, dtype=np.uint8)
        cols_dim = (cols.astype(np.float32) * HIST_DIM).clip(0, 255).astype(np.uint8)
        pcd_bright[idx] = cols
        pcd_dim[idx] = cols_dim
        if idx == t_src:
            pcd_tsrc_tint[idx] = _tint_colors(cols)
        pcd_handles[idx] = server.scene.add_point_cloud(
            f"/pointmap/frame_{idx:04d}",
            points=pts,
            colors=cols,
            point_size=gui_pt_size.value,
        )

    # ── Per-frame dynamic markers (e.g., trajectory endpoints) ───────────────
    marker_handles: dict = {}
    marker_orig_cols: dict = {}   # idx -> (M, 3) uint8 — original per-marker colors
    marker_tint_cols: dict = {}   # idx -> (M, 3) uint8 — dark-red tinted copy
    MARKER_TINT_RGB = np.array([110, 30, 30], dtype=np.uint8)

    def _ensure_marker(idx: int):
        if marker_loader is None or idx in marker_handles:
            return
        pts, cols = marker_loader(idx)
        pts = np.asarray(pts, dtype=np.float32)
        cols = np.asarray(cols, dtype=np.uint8)
        if len(pts) == 0:
            marker_handles[idx] = None
            return
        marker_orig_cols[idx] = cols
        marker_tint_cols[idx] = np.tile(MARKER_TINT_RGB, (len(cols), 1))
        marker_handles[idx] = server.scene.add_point_cloud(
            f"/markers/frame_{idx:04d}",
            points=pts,
            colors=cols,
            point_size=gui_pt_size.value,
            visible=False,
        )

    def refresh_markers():
        if marker_loader is None:
            return
        cur = int(gui_frame.value)
        show = gui_show_markers.value
        tint = gui_tint_markers.value
        _ensure_marker(cur)
        for i, h in marker_handles.items():
            if h is None:
                continue
            is_cur = (i == cur)
            h.visible = show and is_cur
            if h.visible:
                h.colors = marker_tint_cols[i] if tint else marker_orig_cols[i]
                h.point_size = gui_pt_size.value

    def refresh_pcds():
        if pointmap_loader is None:
            return
        cur = int(gui_frame.value)
        sub = max(int(gui_stride.value), 1)
        show_cur = gui_show_pmap.value
        show_tsrc = gui_anchor_tsrc.value
        # Decouple t_src and current visibility:
        # - `Pointmap (current frame)` toggles cur + (when accumulate) history.
        # - `Always Show t_src Pointmap` independently toggles t_src.
        anchors: set[int] = set()
        if show_cur:
            anchors.add(cur)
        if show_tsrc:
            anchors.add(t_src)
        if gui_accumulate.value and show_cur:
            frames_to_show = set(range(0, cur + 1, sub)) | anchors
        else:
            frames_to_show = set(anchors)
        for i in frames_to_show:
            _ensure_pcd(i)
        for i, h in pcd_handles.items():
            in_show = i in frames_to_show
            h.visible = in_show
            h.point_size = gui_pt_size.value
            if in_show:
                if i in anchors:
                    if i == t_src and gui_recolor_tsrc.value and i in pcd_tsrc_tint:
                        h.colors = pcd_tsrc_tint[i]
                    else:
                        h.colors = pcd_bright[i]
                else:
                    h.colors = pcd_dim[i]

    # ── Trajectory line segments ─────────────────────────────────────────────
    track_handles: dict = {name: None for name in cat_names}

    def _refresh_one(name: str):
        h = track_handles[name]
        if h is not None:
            h.remove()
            track_handles[name] = None
        if not gui_show_track[name].value:
            return
        d = trajectories[name]
        wp = d["world_pos"]
        if wp.shape[0] == 0:
            return
        sub = max(int(gui_subsample.value), 1)
        wp_sub = wp[::sub]
        bc_sub = d["colors"][::sub]
        cur = int(gui_frame.value)
        if gui_partial_traj.value:
            # Pairwise mode: 1 straight segment per query, t_src → cur
            if cur == t_src:
                pts, cols = None, None
            else:
                starts = wp_sub[:, t_src]                              # (N, 3)
                ends = wp_sub[:, cur]                                  # (N, 3)
                pts = np.stack([starts, ends], axis=1).astype(np.float32)  # (N, 2, 3)
                cols = np.broadcast_to(bc_sub[:, None, :], (len(bc_sub), 2, 3)).astype(np.uint8).copy()
                finite = np.isfinite(pts).all(axis=(1, 2))
                pts = pts[finite] if finite.sum() else None
                cols = cols[finite] if pts is not None else None
        else:
            # Default: growing-history segments [0..cur]
            pts, cols = build_segments_per_pixel(wp_sub, bc_sub, cur - t_src)
        if pts is None or pts.shape[0] == 0:
            return
        track_handles[name] = server.scene.add_line_segments(
            f"/tracks/{name}", points=pts, colors=cols,
            line_width=float(gui_line_width.value),
        )

    def refresh_tracks():
        for name in cat_names:
            _refresh_one(name)

    # ── Camera frustum (optional, optionally per-frame with history) ─────────
    # camera_pose_c2w: (4,4) static OR (T,4,4) per-frame
    # camera_intrinsics: dict static OR list[dict] length T per-frame
    # In per-frame mode, every frame [0..cur] is shown as a frustum:
    #   - current (= t_tgt): blue + image
    #   - t_src: green anchor + image
    #   - other history frames: gray, no image
    frame_nodes: list = []
    frustum_handles: list = []
    refresh_camera = None
    if camera_pose_c2w is not None and camera_intrinsics is not None:
        import cv2

        c2w_arr = np.asarray(camera_pose_c2w, dtype=np.float64)
        per_frame_pose = c2w_arr.ndim == 3
        per_frame_intr = isinstance(camera_intrinsics, (list, tuple))

        def _get_pose(t: int) -> np.ndarray:
            return c2w_arr[t] if per_frame_pose else c2w_arr

        def _get_intr(t: int) -> dict:
            return camera_intrinsics[t] if per_frame_intr else camera_intrinsics

        def _frustum_image_at(t: int) -> np.ndarray | None:
            if image_loader is None:
                return None
            try:
                rgb = image_loader(t)
                K_t = _get_intr(t)
                target_w = 128
                target_h = max(1, int(128 * K_t["h"] / K_t["w"]))
                return cv2.resize(rgb, (target_w, target_h))
            except Exception:
                return None

        COLOR_CURRENT = (100, 100, 255)   # blue
        COLOR_TSRC = (100, 220, 120)       # green
        COLOR_HISTORY = (160, 160, 160)    # gray

        n_cams = T if per_frame_pose else 1

        for i in range(n_cams):
            t_i = i if per_frame_pose else t_src
            c2w_i = _get_pose(t_i)
            K_i = _get_intr(t_i)
            se3 = vt.SE3.from_matrix(c2w_i[:3, :])
            fn = server.scene.add_frame(
                f"/cameras/frame_{i:04d}",
                wxyz=se3.rotation().wxyz,
                position=se3.translation(),
                axes_length=0.0,
                axes_radius=0.0,
            )
            # Image only for t_src + initial-current; intermediate history left blank
            init_img = _frustum_image_at(t_i) if t_i in (t_src,) else None
            init_color = COLOR_TSRC if t_i == t_src else COLOR_HISTORY
            fh = server.scene.add_camera_frustum(
                f"/cameras/frame_{i:04d}/frustum",
                fov=2.0 * np.arctan(K_i["h"] / (2.0 * K_i["fy"])),
                aspect=K_i["w"] / K_i["h"],
                scale=0.3,
                color=init_color,
                image=init_img,
                line_width=1.5,
            )
            frame_nodes.append(fn)
            frustum_handles.append(fh)

            def _attach_click(fh_=fh, fn_=fn):
                @fh_.on_click
                def _(_):
                    for client in server.get_clients().values():
                        client.camera.wxyz = fn_.wxyz
                        client.camera.position = fn_.position

            _attach_click()

        # Backwards-compat aliases (single-cam consumers expect these names)
        frame_node = frame_nodes[0] if frame_nodes else None
        frustum_handle = frustum_handles[0] if frustum_handles else None

        # Track previous current frame so we can reset its color on transition
        _prev_cur = [t_src]

        def refresh_camera() -> None:
            if not per_frame_pose:
                # Static mode: nothing to update beyond initial pose.
                return
            cur = int(gui_frame.value)
            show = gui_show_camera.value

            # Reset previous current frustum (unless it was t_src — keep green)
            prev = _prev_cur[0]
            if prev != t_src and 0 <= prev < n_cams:
                frustum_handles[prev].color = COLOR_HISTORY
                frustum_handles[prev].image = None

            # Update current
            if 0 <= cur < n_cams:
                if cur == t_src:
                    frustum_handles[cur].color = COLOR_TSRC
                else:
                    frustum_handles[cur].color = COLOR_CURRENT
                img = _frustum_image_at(cur)
                if img is not None:
                    frustum_handles[cur].image = img

            _prev_cur[0] = cur

            # Visibility — history up to cur, plus t_src (always within range)
            for i in range(n_cams):
                visible = show and (i <= cur or i == t_src)
                frustum_handles[i].visible = visible
                frame_nodes[i].visible = visible

        @gui_show_camera.on_update
        def _(_):
            # Trigger refresh; visibility logic lives inside refresh_camera
            if refresh_camera is not None:
                refresh_camera()
            # For static single-frustum mode, just toggle directly
            if not per_frame_pose and frustum_handle is not None:
                frustum_handle.visible = gui_show_camera.value
                frame_node.visible = gui_show_camera.value

    # Image Panel was created earlier (right after frame controls);
    # refresh_images() needs gui_subsample/gui_frame which are already defined.
    def refresh_images():
        if image_loader is None or src_img_handle is None:
            return
        sub = max(int(gui_subsample.value), 1)
        src_img_handle.image = _annotated_src(sub)
        cur_img_handle.image = _ensure_rgb(int(gui_frame.value))
        if overlay_img_handle is not None and overlay_loader is not None:
            overlay_img_handle.image = overlay_loader(int(gui_frame.value))

    # ── Initial render ───────────────────────────────────────────────────────
    refresh_pcds()
    refresh_tracks()
    refresh_images()
    refresh_markers()
    if refresh_camera is not None:
        refresh_camera()

    # ── GUI handlers ─────────────────────────────────────────────────────────
    @gui_frame.on_update
    def _(_):
        refresh_pcds()
        refresh_tracks()
        refresh_images()
        refresh_markers()
        if refresh_camera is not None:
            refresh_camera()

    @gui_show_pmap.on_update
    def _(_):
        refresh_pcds()

    @gui_anchor_tsrc.on_update
    def _(_):
        refresh_pcds()

    @gui_recolor_tsrc.on_update
    def _(_):
        refresh_pcds()

    @gui_accumulate.on_update
    def _(_):
        refresh_pcds()

    @gui_partial_traj.on_update
    def _(_):
        refresh_tracks()

    for name in cat_names:
        @gui_show_track[name].on_update
        def _(_, _name=name):
            _refresh_one(_name)

    @gui_show_markers.on_update
    def _(_):
        refresh_markers()

    @gui_tint_markers.on_update
    def _(_):
        refresh_markers()

    @gui_subsample.on_update
    def _(_):
        refresh_tracks()
        refresh_images()

    @gui_line_width.on_update
    def _(_):
        refresh_tracks()

    @gui_pt_size.on_update
    def _(_):
        for h in pcd_handles.values():
            h.point_size = gui_pt_size.value
        for h in marker_handles.values():
            if h is not None:
                h.point_size = gui_pt_size.value

    @gui_next.on_click
    def _(_):
        gui_frame.value = min(T - 1, int(gui_frame.value) + int(gui_stride.value))

    @gui_prev.on_click
    def _(_):
        gui_frame.value = max(0, int(gui_frame.value) - int(gui_stride.value))

    @gui_reset.on_click
    def _(_):
        gui_frame.value = t_src
        gui_stride.value = 1
        gui_show_pmap.value = True
        gui_accumulate.value = False
        gui_partial_traj.value = False
        gui_subsample.value = 8
        gui_pt_size.value = 0.005
        for cb in gui_show_track.values():
            cb.value = True
        # Reset camera: frame the scene (centered on scene_focus, pulled back
        # by ~2× scene_radius). DO NOT use frame_node.position — capture cam
        # may be far from the action.
        for client in server.get_clients().values():
            client.camera.position = _initial_cam_pos
            client.camera.look_at = tuple(scene_focus)
        refresh_pcds()
        refresh_tracks()
        refresh_images()
        refresh_markers()

    @server.on_client_connect
    def _(client):
        # Up direction: convert "-y" / "+y" / "+z" string to tuple
        up_vec = {
            "+y": (0, 1, 0), "-y": (0, -1, 0),
            "+x": (1, 0, 0), "-x": (-1, 0, 0),
            "+z": (0, 0, 1), "-z": (0, 0, -1),
        }.get(up, (0, 1, 0))
        client.camera.up_direction = up_vec
        # Auto-center: always position at scene_focus + pull-back (don't track
        # frame_node which may be far from scene for static captures).
        client.camera.position = _initial_cam_pos
        client.camera.look_at = tuple(scene_focus)

    # ── Play loop (background thread, advance frame at FPS) ──────────────────
    _play_stop = threading.Event()

    def _play_thread():
        while not _play_stop.is_set():
            if gui_play.value:
                cur = int(gui_frame.value)
                step = max(int(gui_stride.value), 1)
                nxt = cur + step
                if nxt > T - 1:
                    gui_play.value = False  # stop at end (loop disabled — change to nxt = nxt % T to loop)
                    continue
                gui_frame.value = nxt
                # frame's on_update handler triggers refresh_pcds/tracks/images automatically
            fps = max(int(gui_fps.value), 1)
            _play_stop.wait(timeout=1.0 / fps)

    play_thr = threading.Thread(target=_play_thread, daemon=True)
    play_thr.start()

    print(f"[traj_viewer] ready: http://localhost:{port}", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _play_stop.set()
