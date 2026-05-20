---
name: Markdown writing style — TOC + bilingual + structural conventions
description: When writing .md docs, follow user's bilingual academic-blog style with clickable TOC, 中文 prose, English for code/identifiers/math, and consistent header structure
type: feedback
---

When creating or fully rewriting any `.md` document for the user (research notes, system docs, paper notes, project READMEs, etc.), follow this style. Reference: `~/code/imp_genai-d4rt-v1/research/scene4d/feed_forward_tracker/docs/{harness,workflow,repo-structure}.md` are canonical examples.

## Required structure (top to bottom)

1. **Title** — single `#` heading
2. **Blockquote header** immediately after the title — short context: scope, audience, related docs (linked). 1–4 lines. Example:
   ```markdown
   > 当前 `feed_forward_tracker/` 的目录布局约定 + 新文件放置决策表。
   > **注入时机**：任何 D4RT / tracker 相关 edit 前由 ... rule 强制加载。
   > 同类文档：[harness.md](./harness.md)（harness 配置全貌）。
   ```
3. **`## Table of Contents`** — clickable anchor list. Format:
   ```markdown
   ## Table of Contents
   
   - [Section name](#section-name)
   - [Another Section](#another-section)
     - [Subsection](#subsection)
   ```
   Use lowercase, hyphenate spaces; for 中文 anchors GitHub auto-handles them (just lowercase ASCII / leave 中文 as-is). When in doubt, **mirror the heading text exactly** in the link target.
4. **`---`** horizontal rule between TOC and body.
5. **Body** — sections at `##` / subsections at `###`. Numbered (`### A. ...`, `### §1 ...`) when sequence matters.

Skip the TOC only for files with **fewer than 3 sections** (very short README stubs).

## Bilingual rule

- **Body prose, transitions, explanations, motivation, "why" reasoning → 中文**.
- **Stay in English**:
  - Identifiers, variable names, function names, class names, file paths
  - Code blocks (Python, YAML, JSON, shell, etc.)
  - Math formulas / LaTeX
  - Library / framework / tool names (PyTorch, OpenCV, MetaHuman, MRG, ...)
  - Established CV / ML terminology when the English term is more precise (encoder, transformer, attention, BRDF, Cryptomatte, PINHOLE, sRGB, etc.) — don't force translate
  - Acronyms (UE, GT, FPS, VRAM, NPY, EXR, ...)
- **Headings**: prefer 中文 for descriptive headings (e.g. `## 全局视图`, `### 强制流程`), but English when the heading is itself a technical name (e.g. `### TAPVid-3D benchmark`, `### convert_exr.py`).
- **Tables** — column headers usually English (technical), cell content can mix. Don't translate technical labels in tables just to translate.
- **Code comments inside code blocks** — leave English (matches the code's actual style).

The vibe should match `harness.md`'s "Academic + Blog" register: deeply analytical, well-structured, but readable. Not formal academic. Use first-person plural (`我们`) sparingly; usually direct address ("你") is fine.

## Layout conventions

- **Tables** for any side-by-side comparison (3+ items with same fields) — better than bullet lists for scanning.
- **Code fences** with language tag (`bash`, `python`, `yaml`, `json`, `markdown`, `text`).
- **Inline `code`** for: file names, identifiers, shell commands, short literals, env var names, JSON keys.
- **Bold `**foo**`** for emphasizing a key term in 中文 prose. Don't bold long phrases.
- **Blockquote `>`** for: callouts, warnings, "why this exists", related-doc pointers.
- **Horizontal rule `---`** between major sections (especially after TOC, before / between top-level `##` blocks when they're each substantial).
- **Tree diagrams** in fenced ` ```text ` or unfenced — annotate each line with `# inline comment`.
- **Mermaid diagrams** for data flow / architecture — already in the existing `~/.claude/CLAUDE.md` Documentation section.
- **Tensor shapes** annotated as `(B, N, 3)` inline; in tables put shape in its own column.

## Don't

- Don't translate code comments / variable names just to be 中文.
- Don't write Chinglish — when writing 中文 sentences, keep them grammatical 中文; when introducing English terms inline, integrate naturally (e.g. "用 `transformer encoder` 处理 token", not "transformer 编码 the tokens").
- Don't write a TOC longer than the body.
- Don't repeat the title verbatim as the first `##`.
- Don't put massive code dumps (>200 lines) inline — link them or summarize.
- Don't use emoji headings unless the user uses them in their prompt.
