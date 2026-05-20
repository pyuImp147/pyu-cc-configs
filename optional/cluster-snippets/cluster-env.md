# Cluster Snippet — SLURM / Conda / Shared Storage

> Append to `~/.claude/CLAUDE.md` **only when running on a CoreWeave-style SLURM cluster**.
> Skip entirely on mac / non-cluster hosts.

合并来源：
- 原 `~/.claude/CLAUDE.md` 中 `## SLURM Cluster (CoreWeave)` 整段
- 原 `~/.claude/cluster_env.md` 完整内容
- 原 CLAUDE.md `## Safety` 中 `/mnt/data/` `/mnt/home/pengcheng.yu/` 两条 cluster-coupled rule

---

## SLURM Cluster (CoreWeave)

### Hardware

| | H100 | RTX Pro 6000 |
|---|---|---|
| **Partition** | `h100` | `rtxp6000` |
| **Nodes** | 31 | 39 |
| **Architecture** | Hopper | Blackwell |
| **GPU** | 8× H100 80GB HBM3 | 8× RTX Pro 6000 96GB GDDR7 |
| **CPUs/node** | 128 | 128 |
| **RAM/node** | ~2 TB | ~1 TB |
| **GRES** | `gpu:h100:N` | `gpu:nvidia_rtx_pro_6000_blackwell_server_edition:N` (or `gpu:N` on `rtxp6000` partition) |

- **Shared storage**: `/mnt/data/` (models, wheels, datasets)
- **Home**: `/mnt/home/<user>/`
- **Default partition**: `all*` includes both GPU types — always specify `-p h100` or `-p rtxp6000`

### GPU Selection
- **RTX Pro 6000**: development, debugging, small experiments, HP sweeps, inference, when H100 busy
- **H100**: large model training, high memory bandwidth workloads, multi-node DDP, FP8 training, max throughput

### Resource Proportions
- 1 GPU: 16 CPUs, 128G (h100) / 64G (rtxp6000)
- 4 GPUs: 64 CPUs, 512G (h100) / 256G (rtxp6000)
- 8 GPUs (full node): 128 CPUs, 1984G (h100) / 956G (rtxp6000)

### Rules
- NEVER run GPU-intensive tasks on login node
- Training/inference MUST go through `sbatch` or `srun`
- Always specify partition explicitly (`-p h100` or `-p rtxp6000`)
- Always use random MASTER_PORT: `$(shuf -i 29500-29999 -n 1)`
- Always include checkpoint resume logic in training scripts
- Submit jobs from repository root (`$SLURM_SUBMIT_DIR`)
- **Resource reporting**: ALWAYS use `scontrol show job $SLURM_JOB_ID | grep mem` to check actual cgroup limits. NEVER use `free -h` — it shows physical node memory, not the job's allocation. Same for CPUs: check `scontrol` not `nproc`.

### Environment
- **Conda env**: `imp_genai` (Python 3.10), user env at `~/.conda/envs/`
- **Conda base**: `/opt/conda` (system-level, read-only, no write permission)
- **Activation**: `conda activate imp_genai` (from scripts: `source ~/.bashrc && conda activate imp_genai`)
- **PyTorch**: 2.9.0+cu128 | **CUDA**: 12.8 | **cuDNN**: 9.10.02
- **HF_HOME**: `/mnt/data/models/huggingface` (shared cache)
- **Blackwell compatibility**: CUDA 12.4+, PyTorch 2.6+ (current env satisfies both)

---

## Cluster-Specific Safety Rules

- **`/mnt/data/` is shared storage** — NEVER delete anything under it. Writing/creating files there requires explicit user confirmation first.
- **`/mnt/home/pengcheng.yu/`** — free to read/write.

---

## Full CoreWeave Reference (formerly `~/.claude/cluster_env.md`)

### Cluster Overview

| | H100 Partition | RTX Pro 6000 Partition |
|---|---|---|
| **Partition name** | `h100` | `rtxp6000` |
| **Nodes** | 31 | 39 |
| **Architecture** | Hopper | Blackwell |
| **GPU per node** | 8× NVIDIA H100 80GB HBM3 | 8× NVIDIA RTX Pro 6000 Blackwell Server Edition |
| **GPU VRAM** | 80 GB HBM3 | 96 GB GDDR7 |
| **CPUs per node** | 128 (2 sockets) | 128 (2 sockets) |
| **RAM per node** | ~1984 GB (~2 TB) | ~956 GB (~1 TB) |
| **GRES name** | `gpu:h100` | `gpu:nvidia_rtx_pro_6000_blackwell_server_edition` |
| **CUDA requirement** | CUDA 12.1+ | CUDA 12.4+ (Blackwell) |
| **Default partition** | `all*` includes both | `all*` includes both |

### GPU Selection Guide

#### Use RTX Pro 6000 (`rtxp6000`) for:
- Development and debugging (more available nodes)
- Smaller experiments and hyperparameter sweeps
- Inference workloads
- When H100 nodes are busy
- Tasks that benefit from larger per-GPU VRAM (96 GB vs 80 GB)

#### Use H100 (`h100`) for:
- Large model training (LLMs, diffusion models)
- Workloads requiring high memory bandwidth (HBM3)
- Multi-node distributed training
- FP8 training (native hardware support)
- Maximum training throughput

#### Key Differences
- **H100** has HBM3 with ~3.35 TB/s bandwidth — critical for memory-bound ops (attention, large batch norms)
- **RTX Pro 6000** has GDDR7 with lower bandwidth but 20% more VRAM per GPU
- **H100** has native FP8 Transformer Engine — 2× throughput for supported ops
- **RTX Pro 6000** Blackwell has improved FP4/FP8 but different Transformer Engine support
- **H100** nodes have 2× system RAM (~2TB vs ~1TB) — matters for CPU-heavy data loading

### Resource Allocation Templates

#### Proportional resource allocation per GPU:

| GPUs | Partition | CPUs | RAM | Example |
|------|-----------|------|-----|---------|
| 1 | h100 | 16 | 128-256G | Development, single-GPU training |
| 1 | rtxp6000 | 16 | 64-128G | Debugging, inference |
| 4 | h100 | 64 | 512G | Multi-GPU training |
| 4 | rtxp6000 | 64 | 256-512G | HP sweeps, medium training |
| 8 | h100 | 128 | 1984G | Full node, large model training |
| 8 | rtxp6000 | 128 | 956G | Full node |

#### SLURM submission examples:

```bash
# Single H100
srun -p h100 --gres=gpu:h100:1 -c 16 --mem=128G -t 2-00:00:00 --pty bash

# Single RTX Pro 6000
srun -p rtxp6000 --gres=gpu:1 -c 16 --mem=64G -t 2-00:00:00 --pty bash

# 4× H100 for DDP training
sbatch -p h100 --gres=gpu:h100:4 -c 64 --mem=512G -t 2-00:00:00 train.sh

# 4× RTX Pro 6000 for HP sweep
sbatch -p rtxp6000 --gres=gpu:4 -c 64 --mem=256G -t 2-00:00:00 sweep.sh
```

Note: On `rtxp6000` partition, `--gres=gpu:N` suffices (only one GPU type). On `h100` partition or `all*`, specify `gpu:h100:N` explicitly.

### Conda Environment: `imp_genai`

| Component | Version |
|-----------|---------|
| Python | 3.10 |
| PyTorch | 2.9.0+cu128 |
| CUDA (toolkit) | 12.8 |
| cuDNN | 9.10.02 |
| Location | `~/.conda/envs/imp_genai` |

#### Other environments
- `imp_sam3d` — SAM3D project
- `sam3d` — SAM3D alternate
- `tb` — TensorBoard

#### Activation
```bash
conda activate imp_genai
# Or from scripts:
source ~/.bashrc && conda activate imp_genai
```

#### Shared paths
- **HF_HOME**: `/mnt/data/models/huggingface` (shared model cache)
- **Pre-built wheels**: `/mnt/data/wheels/`
- **Shared datasets**: `/mnt/data/`
- **Conda base**: `/opt/conda` (system-level, read-only)

### Package Management Rules

#### NEVER use conda-forge for CUDA packages
- PyTorch, torchvision, torchaudio → official PyTorch wheel index
- xformers → official PyTorch wheel index
- pytorch3d → build from source
- Any CUDA-dependent package → pip

#### Always use official PyTorch wheel index
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install xformers --index-url https://download.pytorch.org/whl/cu128
pip install --no-build-isolation git+https://github.com/facebookresearch/pytorch3d.git@stable
```

#### Safe conda-forge packages
- `ffmpeg`, pure Python packages, system utilities

### GPU Architecture & CUDA Compatibility

| Architecture | GPUs | Min CUDA | Min PyTorch |
|---|---|---|---|
| Blackwell | RTX Pro 6000, B100, B200 | 12.4 | 2.6 |
| Hopper | H100, H200 | 12.1 | 2.0 |
| Ampere | A100, A40 | 11.8 | 1.10 |

### Environment Recovery

If conda env gets corrupted (ABI errors, missing torch attributes, import failures):

```bash
conda deactivate
conda env remove -n imp_genai -y
# Rebuild from install scripts
```

Don't try to fix in place — rebuild is faster and more reliable.
