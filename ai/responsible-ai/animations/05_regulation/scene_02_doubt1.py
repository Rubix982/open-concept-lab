"""
scene_02_doubt1.py

Doubt 1 — Regulators don't understand what they're regulating.
Response — Law provides consistency that nothing else reliably does.
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


class Doubt1Competence(Scene):
    """Doubt 1 — Regulatory competence."""

    def construct(self) -> None:
        self._doubt()
        self._response()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 1 of 6",
            header_text="Regulators don't understand what they're regulating.",
            examples=[
                (
                    "2018 — Senator to Zuckerberg:",
                    '"How does Facebook make money if users don\'t pay?"',
                ),
                (
                    "2023 — Congressional AI hearings:",
                    "Basic questions about how large language models work.",
                ),
                (
                    "The pattern:",
                    "Those deciding the rules are often furthest from the technology.",
                ),
                (
                    "The Collingridge Dilemma:",
                    "Too early = effects unknown. Too late = too embedded to fix.",
                ),
            ],
            closing_text="These are the people writing the rules.",
        )

    def _response(self) -> None:
        # Response header
        resp_header: Text = Text(
            "Response — Law provides what nothing else reliably does.",
            font_size=28,
            color=GREEN_D,
            weight=BOLD,
        )
        resp_header.to_edge(UP, buff=0.55)
        self.play(Write(resp_header), run_time=0.9)
        self.wait(0.3)

        # Response points
        points: list[tuple[str, str]] = [
            (
                "Markets self-regulate poorly.",
                "They hold themselves accountable rarely — by design.",
            ),
            (
                "Norms are slow and uneven.",
                "Social pressure works across decades, not product cycles.",
            ),
            (
                "Architecture is the thing under discussion.",
                "You can't rely on the system to regulate itself.",
            ),
            (
                "Law is the reasonable default — not because it's perfect,",
                "but because the alternatives have well-documented failure modes.",
            ),
            (
                "The answer to incompetence:",
                "Build regulatory capacity. Don't abandon regulation.",
            ),
        ]

        example_mobs: list[VGroup] = [
            make_example_block(label, detail) for label, detail in points
        ]
        start_pos = resp_header.get_bottom() + DOWN * 0.6 + LEFT * 5.5
        stacked: VGroup = stack_bullets(example_mobs, start=start_pos, spacing=0.6)

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
