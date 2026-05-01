"""
scene_03_doubt2.py

Doubt 2 — Regulation has real costs.
Response — The protections we rely on daily were fought by industry for decades.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from manim import *  # noqa: E402
from shared.lecture import (  # noqa: E402
    animate_doubt_scene,
    make_header,
    make_example_block,
    make_closing,
    stack_bullets,
)


class Doubt2Cost(Scene):
    """Doubt 2 — Regulation costs."""

    def construct(self) -> None:
        self._doubt()
        self._response()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 2 of 6",
            header_text="Regulation has real costs.",
            examples=[
                (
                    "Compliance burden:",
                    "Falls disproportionately on smaller actors with fewer resources.",
                ),
                (
                    "Agency creation:",
                    "Building regulatory bodies takes time, money, and expertise.",
                ),
                (
                    "Discretion shrinks:",
                    "Every rule limits what individuals and organisations can do.",
                ),
                (
                    "Power concentration:",
                    "New regulatory powers can be wielded against those they weren't meant for.",
                ),
            ],
            closing_text="Costs are real. They need to be weighed, not assumed away.",
        )

    def _response(self) -> None:
        resp_header: Text = Text(
            "Response — The protections we rely on were fought tooth and nail.",
            font_size=26,
            color=GREEN_D,
            weight=BOLD,
        )
        resp_header.to_edge(UP, buff=0.55)
        self.play(Write(resp_header), run_time=0.9)
        self.wait(0.3)

        points: list[tuple[str, str]] = [
            (
                "Seatbelts and airbags:",
                "Auto industry opposed them for decades. Now saves ~15,000 lives/year in the US.",
            ),
            (
                "Pharmaceutical testing:",
                "Industry fought requirements. Thalidomide is why they exist.",
            ),
            (
                "Building fire codes:",
                "Triangle Shirtwaist Factory, 1911 — 146 workers died. Codes followed.",
            ),
            (
                "Food labeling standards:",
                "Industry called them burdensome. Consumers call them basic.",
            ),
            (
                "The pattern:",
                "Every major safety protection was 'too costly' until it wasn't.",
            ),
        ]

        example_mobs: list[VGroup] = [
            make_example_block(label, detail) for label, detail in points
        ]
        start_pos = resp_header.get_bottom() + DOWN * 0.6 + LEFT * 5.5
        stacked: VGroup = stack_bullets(example_mobs, start=start_pos, spacing=0.58)

        for mob in example_mobs:
            self.play(FadeIn(mob, shift=RIGHT * 0.15), run_time=0.45)
            self.wait(0.35)

        self.wait(0.3)

        closing: Text = make_closing(
            "Skepticism about regulation is skepticism about public safety."
        )
        closing.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(closing, shift=UP * 0.1))
        self.wait(2.0)

        self.play(
            FadeOut(resp_header),
            FadeOut(stacked),
            FadeOut(closing),
            run_time=0.7,
        )
