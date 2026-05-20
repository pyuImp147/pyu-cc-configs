#!/usr/bin/env python3
"""Synthetic demo: helix + static grid trajectories, no external data needed.

Demonstrates the dataset-agnostic API: caller produces (N, T, 3) arrays from
ANY source — here we just generate analytic motion. Run:

    python examples/demo_synthetic.py --share

You'll get a public viser.studio share-link with two categories of trajectories
(`helix` moving + `static` not), a synthetic per-frame pointmap, and the full
GUI (frame slider / stride / accumulate / per-category visibility / etc.).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

# Allow `python examples/demo_synthetic.py` from skill root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from traj_viewer import launch_traj_viewer  # noqa: E402


def make_helix_trajectories(N: int, T: int) -> np.ndarray:
    """N points on a helix, advancing along Z over T frames. Returns (N, T, 3)."""
    phi0 = np.linspace(0, 2 * np.pi, N, endpoint=False)
    out = np.empty((N, T, 3), dtype=np.float32)
    for t in range(T):
        phi = phi0 + 0.1 * t
        z = -1.0 + 0.05 * t
        out[:, t, 0] = np.cos(phi) * 0.8
        out[:, t, 1] = np.sin(phi) * 0.8
        out[:, t, 2] = z
    return out


def make_static_grid(M: int, T: int) -> np.ndarray:
    """M×M grid of static points (degenerate trajectories). Returns (M*M, T, 3)."""
    g = np.linspace(-2, 2, M)
    xx, zz = np.meshgrid(g, g)
    pts = np.stack([xx.ravel(), np.full(M * M, -1.5), zz.ravel()], axis=1).astype(np.float32)
    return np.broadcast_to(pts[:, None, :], (M * M, T, 3)).copy()


def make_pointmap(frame_idx: int, T: int) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic per-frame pointmap: 5000 random points in a slowly drifting cube."""
    rng = np.random.default_rng(seed=frame_idx)
    pts = rng.uniform(-2.5, 2.5, size=(5000, 3)).astype(np.float32)
    pts[:, 0] += 0.01 * frame_idx  # subtle drift
    cols = (rng.uniform(50, 256, size=(5000, 3))).astype(np.uint8)
    return pts, cols


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8893)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--T", type=int, default=30)
    args = parser.parse_args()

    T = args.T
    helix_world = make_helix_trajectories(200, T)
    static_world = make_static_grid(20, T)

    # Provide synthetic uvs so colors auto-derive from per_uv_base_colors
    helix_uvs = np.stack(
        [np.linspace(50, 974, 200).astype(int), np.full(200, 200, dtype=int)], axis=1
    )
    static_uvs = np.stack(
        np.meshgrid(np.linspace(20, 1004, 20).astype(int), np.linspace(400, 700, 20).astype(int)),
        axis=-1,
    ).reshape(-1, 2)

    trajectories = {
        "helix": {"world_pos": helix_world, "uvs": helix_uvs},
        "static_grid": {"world_pos": static_world, "uvs": static_uvs},
    }

    launch_traj_viewer(
        trajectories=trajectories,
        T=T,
        pointmap_loader=lambda idx: make_pointmap(idx, T),
        image_size=(1024, 750),
        t_src=0,
        up="-y",
        port=args.port,
        share=args.share,
        title="Synthetic Trajectory Demo (helix + static grid)",
    )


if __name__ == "__main__":
    main()
