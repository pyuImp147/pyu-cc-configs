---
name: data-convention-direct-test
description: "When verifying a data-convention claim (pixel-centric / axis-order / coord-system / unit), build a raw-input → physical-output end-to-end closed-loop test from the canonical schema. Do NOT cite preprocess/loader/sanity-check code that the team itself wrote — that is circular indirect evidence."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f0346385-b1aa-4b05-b48f-344befaf191b
---

**Rule**: 验证一个 data-convention 类的 claim（像素 `+0.5` / axis-order yxz vs xyz / coord 系 OpenCV vs OpenGL vs Blender / depth 单位 metric vs uint16 raw / quaternion (w,x,y,z) vs (x,y,z,w) / homogeneous 是行向量还是列向量）时，必须构造**从 raw input 端到 physical output 端的闭环 numerical test**。证据来源限定在：(1) 数据集 / SDK 的官方 schema / docs，(2) 第一性原理的 camera / geometry math。

**绝不**用以下"间接证据"论证 axis 语义：

- 项目内 preprocess 代码（即使 file header 写 "Copyright <Vendor> Authors"，整文件也可能被本团队 heavily modified）
- 项目内 dataloader 代码
- 项目内 sanity-check / numpy verification block（也是咱自己写的，可能本身 bug）
- 输出端 observation（"我看 queries 的小数部分都是 .5" —— 这只证明"上游加了 0.5"，不证明"axis 原本就是 center"）
- 别的 paper / project 的"通常做法"

**Why**: 2026-05-17 验证 Kubric `object_coordinates[t, y, x]` axis 是 pixel-center 还是 pixel-corner 时，我先后用了三种"证据"全部被 user 戳穿是间接证据：(a) `dataset_mix_3d.py:843 pixel_to_raster=[0,0.5,0.5]` —— 循环论证；(b) `dataset_mix_3d.py:1788-1827` reproject numpy check —— 也是咱自己写的；(c) processed `.npy` queries 全 `.5` —— 输出端 observation。User 一句话点穿："最直接的办法，随便取一个 image，根据 object coordinate 拿到 world pos，根据 camera reproject，看得到的 points2d 是 [u,v] 还是 [u+0.5, v+0.5]"。Hallucinate 了 3 轮才落到 raw TFRecord 直接验证（`0_debug/sanity_check/verify_kubric_pixel_axis.py`），实测 `||uv−(x+.5, y+.5)||` mean=0.0016 vs `||uv−(x, y)||` mean=0.7069 ≈ √2/2。

**How to apply**:

- 用户问"X 数据集的 Y convention 是什么 / 验证 Y 是 A 还是 B"时，先识别这是 data-convention 问题（不是 paper 内容问题，paper-evidence 流程不适用）。
- 直接给出闭环实验设计：raw input 路径 + canonical decode + 第一性原理 forward math + 比较 output。**不要**先去 grep 项目内代码再"推理"。
- 实验代码独立、最小、可复跑：从 raw 数据集 loader（`tfds.load` / `torch.utils.data.Dataset` 官方 builder / `h5py.File` 等）读 schema，禁止 import 项目内 preprocess module。
- 落脚一个 standalone script（命名 `verify_<dataset>_<convention>.py`，放 `0_debug/sanity_check/` 或类似），实测数字写进 doc 和 CHANGELOG，script 留作 regression check。
- 真不知道时直接说"我没有直接证据，需要跑一个闭环实验"，不要从 preprocess 代码硬推。

**Trigger keywords**: `+0.5` / pixel-center / pixel-corner / axis convention / row-major vs col-major / opencv vs opengl / quaternion convention / coord system verification / 验证 axis / 验证约定 / "是不是 +0.5"
