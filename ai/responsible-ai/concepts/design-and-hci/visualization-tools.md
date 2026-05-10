# Visualization Tools for Concept Mapping

Notes on tools evaluated for generating concept maps, knowledge graphs, and animated diagrams for course notes.

## Current Choice — Mermaid (interim)

Embedded in Markdown. Good for quick iteration, readable in GitHub and most editors. Output is rigid — layout is auto-generated, not natural.

**Use when:** capturing a concept map quickly alongside prose notes.

---

## Better Alternatives for Visual Quality

### Excalidraw

- Hand-drawn aesthetic, feels organic
- Open source, web-based, Obsidian plugin available
- Good for quick sketches and whiteboard-style maps
- Export to SVG/PNG

### Kumu

- Purpose-built for systems thinking and relationship maps
- Most visually polished tool in this space
- Used in research and strategy contexts
- Free tier available

### Heptabase

- Card-based canvas — ideas as cards, visually connected
- Designed for building mental models
- Paid, but suited exactly to this use case

---

## AI-Assisted (Text → Diagram)

### Napkin.ai

- Paste text or an idea, generates a visual concept map
- Most natural-feeling AI diagram output tested
- Worth trying for course concept maps

### Eraser.io

- AI diagram mode with cleaner aesthetic than Mermaid
- Also supports code-based diagrams for precision

### Whimsical

- Mind maps and flowcharts that look genuinely good
- Has AI generation

---

## Programmatic / Animation

### Manim Community Edition (ManimCE)

- Python library by 3Blue1Brown, community fork
- Produces animated mathematical/conceptual visualizations
- Nodes can materialize, edges draw, clusters form progressively
- Output: MP4 or GIF
- Requires: `cairo`, `ffmpeg`, optional LaTeX — all installable via `brew`
- **Planned for this course** — building animated concept maps per topic

**Repo:** `ManimCommunity/manim`

### D3.js (force-directed graphs)

- Fully custom, nodes naturally repel/attract
- Very organic feel, full aesthetic control
- Requires JavaScript

### Graphviz (`neato` / `fdp` layout)

- More organic layout than Mermaid's top-down default
- Good middle ground between code-based and visual

---

## Decision

| Use case                    | Tool                      |
| --------------------------- | ------------------------- |
| Quick inline concept map    | Mermaid (in course notes) |
| Polished standalone map     | Kumu or Excalidraw        |
| Animated course concept map | Manim CE (planned)        |
| AI-generated from prose     | Napkin.ai                 |
