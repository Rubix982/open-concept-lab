"""
model_size_vs_performance.py

Animation comparing small efficient models vs large frontier models.
Part of the Human-Centered AI series (Module 08).

Three-act structure:
  Act I   — Architecture: what a transformer layer is, then stacking layers
  Act II  — Scale comparison: small vs large side by side
  Act III — Performance vs size: small models closing the gap
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # noqa: E402

from manim import *  # noqa: E402
import numpy as np  # noqa: E402

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
SMALL_COLOR: ManimColor = TEAL_D
LARGE_COLOR: ManimColor = RED_D
LAYER_COLOR: ManimColor = BLUE_D
LABEL_COLOR: ManimColor = WHITE
DIM_COLOR: ManimColor = GRAY_B


# ---------------------------------------------------------------------------
# Data (confirmed from official technical reports and public benchmarks)
# ---------------------------------------------------------------------------
SMALL_MODELS: list[dict] = [
    {"name": "Llama 3.2\n3B", "params": 3, "layers": 24, "mmlu": 63.4, "gsm8k": 57.0},
    {
        "name": "Phi-3\nMini 3.8B",
        "params": 3.8,
        "layers": 32,
        "mmlu": 68.8,
        "gsm8k": 82.5,
    },
    {"name": "Mistral\n7B", "params": 7, "layers": 32, "mmlu": 60.1, "gsm8k": 40.3},
    {"name": "Qwen 2.5\n7B", "params": 7, "layers": 28, "mmlu": 74.2, "gsm8k": 85.0},
]

LARGE_MODELS: list[dict] = [
    {
        "name": "Llama 3.1\n405B",
        "params": 405,
        "layers": 126,
        "mmlu": 87.7,
        "gsm8k": 96.8,
    },
    {
        "name": "Claude 3\nOpus",
        "params": 400,
        "layers": 96,
        "mmlu": 86.8,
        "gsm8k": 95.0,
    },
    {"name": "GPT-4o", "params": 200, "layers": 120, "mmlu": 88.7, "gsm8k": 92.0},
    {
        "name": "Claude 3.5\nSonnet",
        "params": 175,
        "layers": 96,
        "mmlu": 90.4,
        "gsm8k": 96.4,
    },
]


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
class ModelSizeVsPerformance(Scene):
    """Small vs large models — layers, scale, and performance gap."""

    def construct(self) -> None:
        self._title()
        self._act_one_transformer_layer()
        self._act_two_scale_comparison()
        self._act_three_performance_gap()
        self.wait(2)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    def _title(self) -> None:
        title: Text = Text("Small Models vs Large Models", font_size=40, color=WHITE)
        sub: Text = Text(
            "Layers, Scale, and the Closing Performance Gap",
            font_size=20,
            color=GRAY,
        )
        sub.next_to(title, DOWN, buff=0.25)
        group: VGroup = VGroup(title, sub)

        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub, shift=UP * 0.1))
        self.wait(0.8)
        self.play(group.animate.scale(0.38).to_corner(UL, buff=0.22))

    # ------------------------------------------------------------------
    # Act I — What is a transformer layer?
    # ------------------------------------------------------------------
    def _act_one_transformer_layer(self) -> None:
        label: Text = Text("Act I — One Transformer Layer", font_size=14, color=GRAY)
        label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(label))

        # Build one layer as a stack of boxes
        components: list[str] = ["Input", "Attention", "Feed Forward", "Output"]
        colors: list[ManimColor] = [GRAY_B, BLUE_D, TEAL_D, GRAY_B]

        boxes: list[VGroup] = []
        for i, (comp, color) in enumerate(zip(components, colors)):
            rect: Rectangle = Rectangle(
                width=3.5,
                height=0.7,
                color=color,
                fill_color=color,
                fill_opacity=0.15,
                stroke_width=2,
            )
            txt: Text = Text(comp, font_size=16, color=color)
            txt.move_to(rect.get_center())
            boxes.append(VGroup(rect, txt))

        layer_group: VGroup = VGroup(*boxes).arrange(DOWN, buff=0.08)
        layer_group.move_to(ORIGIN)

        # Arrows between boxes
        arrows: list[Arrow] = []
        for i in range(len(boxes) - 1):
            a: Arrow = Arrow(
                boxes[i].get_bottom(),
                boxes[i + 1].get_top(),
                buff=0.05,
                stroke_width=1.5,
                tip_length=0.12,
                color=GRAY,
            )
            arrows.append(a)

        for box in boxes:
            self.play(FadeIn(box, shift=UP * 0.1), run_time=0.35)
        for arrow in arrows:
            self.play(Create(arrow), run_time=0.2)

        layer_label: Text = Text(
            "1 Layer", font_size=18, color=LAYER_COLOR, weight=BOLD
        )
        layer_label.next_to(layer_group, RIGHT, buff=0.4)
        self.play(FadeIn(layer_label))
        self.wait(0.8)

        # Collapse to a thin bar
        bar: Rectangle = Rectangle(
            width=3.5,
            height=0.3,
            color=LAYER_COLOR,
            fill_color=LAYER_COLOR,
            fill_opacity=0.4,
            stroke_width=1.5,
        )
        bar.move_to(ORIGIN)

        self.play(
            FadeOut(VGroup(*arrows)),
            Transform(VGroup(*boxes), bar),
            FadeOut(layer_label),
        )

        bar_label: Text = Text("= 1 layer", font_size=15, color=LAYER_COLOR)
        bar_label.next_to(bar, RIGHT, buff=0.3)
        self.play(FadeIn(bar_label))
        self.wait(0.5)
        self.play(FadeOut(VGroup(*boxes), bar, bar_label), FadeOut(label))

    # ------------------------------------------------------------------
    # Act II — Scale comparison
    # ------------------------------------------------------------------
    def _act_two_scale_comparison(self) -> None:
        label: Text = Text("Act II — Scale Comparison", font_size=14, color=GRAY)
        label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(label))

        # Small model stack (24 layers — Llama 3.2 3B)
        small_layers: int = 24
        large_layers: int = 126  # Llama 3.1 405B

        small_stack: VGroup = self._make_layer_stack(
            small_layers, SMALL_COLOR, max_visible=24, width=1.2
        )
        small_stack.move_to(LEFT * 4 + DOWN * 0.5)

        large_stack: VGroup = self._make_layer_stack(
            large_layers, LARGE_COLOR, max_visible=40, width=1.2, compressed=True
        )
        large_stack.move_to(RIGHT * 2 + DOWN * 0.5)

        # Labels
        small_title: Text = Text(
            "Small Model", font_size=18, color=SMALL_COLOR, weight=BOLD
        )
        small_title.next_to(small_stack, UP, buff=0.2)

        small_info: Text = Text(
            "Llama 3.2 3B\n24 layers\n3 billion parameters",
            font_size=13,
            color=DIM_COLOR,
        )
        small_info.next_to(small_stack, DOWN, buff=0.2)

        large_title: Text = Text(
            "Large Model", font_size=18, color=LARGE_COLOR, weight=BOLD
        )
        large_title.next_to(large_stack, UP, buff=0.2)

        large_info: Text = Text(
            "Llama 3.1 405B\n126 layers\n405 billion parameters",
            font_size=13,
            color=DIM_COLOR,
        )
        large_info.next_to(large_stack, DOWN, buff=0.2)

        # Ellipsis for large model
        dots: Text = Text("⋮  (126 total)", font_size=13, color=LARGE_COLOR)
        dots.next_to(large_stack, RIGHT, buff=0.2)

        self.play(
            FadeIn(small_title),
            FadeIn(large_title),
        )
        self.play(
            Create(small_stack),
            Create(large_stack),
            run_time=1.2,
        )
        self.play(
            FadeIn(small_info),
            FadeIn(large_info),
            FadeIn(dots),
        )

        # Parameter ratio callout
        ratio: Text = Text(
            "135× more parameters", font_size=16, color=GOLD_D, weight=BOLD
        )
        ratio.move_to(RIGHT * 2 + UP * 3.2)
        arrow_ratio: Arrow = Arrow(
            small_stack.get_top() + UP * 0.1,
            large_stack.get_top() + UP * 0.1,
            buff=0.1,
            color=GOLD_D,
            stroke_width=1.5,
            tip_length=0.15,
        )
        self.play(Create(arrow_ratio), FadeIn(ratio))
        self.wait(1.5)

        self.play(
            FadeOut(
                VGroup(
                    small_stack,
                    large_stack,
                    small_title,
                    large_title,
                    small_info,
                    large_info,
                    dots,
                    ratio,
                    arrow_ratio,
                )
            ),
            FadeOut(label),
        )

    def _make_layer_stack(
        self,
        n_layers: int,
        color: ManimColor,
        max_visible: int,
        width: float = 1.2,
        compressed: bool = False,
    ) -> VGroup:
        """Stack of thin rectangles representing transformer layers."""
        show: int = min(n_layers, max_visible)
        height: float = 0.1 if compressed else 0.15
        buff: float = 0.03 if compressed else 0.04
        bars: list[Rectangle] = [
            Rectangle(
                width=width,
                height=height,
                color=color,
                fill_color=color,
                fill_opacity=0.5,
                stroke_width=1,
            )
            for _ in range(show)
        ]
        return VGroup(*bars).arrange(DOWN, buff=buff)

    # ------------------------------------------------------------------
    # Act III — Performance gap closing
    # ------------------------------------------------------------------
    def _act_three_performance_gap(self) -> None:
        label: Text = Text(
            "Act III — The Performance Gap Is Closing", font_size=14, color=GRAY
        )
        label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(label))

        # Build bar chart: MMLU scores for all models
        all_models: list[dict] = SMALL_MODELS + LARGE_MODELS
        self._draw_bar_chart(
            models=all_models,
            metric="mmlu",
            metric_label="MMLU Score (%)",
            title="General Knowledge — MMLU Benchmark",
        )
        self.wait(1.5)
        self._clear_chart()

        # GSM8K
        self._draw_bar_chart(
            models=all_models,
            metric="gsm8k",
            metric_label="GSM8K Score (%)",
            title="Math Reasoning — GSM8K Benchmark",
        )
        self.wait(1.5)
        self._clear_chart()

        # Closing observation
        closing: Text = Text(
            "Phi-3 Mini (3.8B): 82.5% on GSM8K.\nGPT-4o: 92%. The gap is real — but not 135×.",  # noqa: E501
            font_size=17,
            color=GOLD_D,
            slant=ITALIC,
        )
        closing.move_to(ORIGIN)
        self.play(FadeIn(closing))
        self.wait(2.0)

        opacity_note: Text = Text(
            "More layers = more capability = more opacity.\nNobody fully understands what happens inside either.",  # noqa: E501
            font_size=15,
            color=GRAY_B,
        )
        opacity_note.next_to(closing, DOWN, buff=0.4)
        self.play(FadeIn(opacity_note))
        self.wait(2.0)
        self.play(FadeOut(VGroup(closing, opacity_note)), FadeOut(label))

    def _draw_bar_chart(
        self,
        models: list[dict],
        metric: str,
        metric_label: str,
        title: str,
    ) -> None:
        """Horizontal bar chart comparing model scores on one benchmark."""
        n: int = len(models)
        bar_height: float = 0.35
        bar_spacing: float = 0.55
        max_width: float = 7.0
        max_val: float = 100.0

        title_mob: Text = Text(title, font_size=20, color=WHITE, weight=BOLD)
        title_mob.to_edge(UP, buff=0.5)
        self.play(Write(title_mob), run_time=0.6)

        start_y: float = (n / 2) * bar_spacing - bar_spacing / 2
        origin_x: float = -5.0

        for i, model in enumerate(models):
            y: float = start_y - i * bar_spacing
            score: float = model[metric]
            bar_w: float = (score / max_val) * max_width
            color: ManimColor = SMALL_COLOR if model in SMALL_MODELS else LARGE_COLOR

            bar: Rectangle = Rectangle(
                width=bar_w,
                height=bar_height,
                color=color,
                fill_color=color,
                fill_opacity=0.7,
                stroke_width=1,
            )
            bar.move_to(np.array([origin_x + bar_w / 2, y, 0]))

            name: Text = Text(model["name"], font_size=11, color=color)
            name.next_to(bar, LEFT, buff=0.1)

            score_label: Text = Text(f"{score}%", font_size=12, color=WHITE)
            score_label.next_to(bar, RIGHT, buff=0.1)

            params: Text = Text(
                f"{model['params']}B params", font_size=10, color=GRAY_B
            )
            params.next_to(score_label, RIGHT, buff=0.2)

            self.play(
                GrowFromEdge(bar, LEFT),
                FadeIn(name),
                FadeIn(score_label),
                FadeIn(params),
                run_time=0.4,
            )

        axis_label: Text = Text(metric_label, font_size=13, color=GRAY)
        axis_label.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(axis_label))

    def _clear_chart(self) -> None:
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
