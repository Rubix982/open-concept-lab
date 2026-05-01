"""
scene_06_doubt5.py

Doubt 5 — The precautionary principle can freeze innovation.
Response — Rules vs. standards. Regulatory sandboxes. The binary is false.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from manim import *  # noqa: E402
from shared.lecture import (  # noqa: E402
    animate_doubt_scene,
    make_example_block,
    make_closing,
    make_header,
    stack_bullets,
)


class Doubt5Precaution(Scene):
    """Doubt 5 — Precautionary principle and innovation."""

    def construct(self) -> None:
        self._doubt()
        self._rules_vs_standards()
        self._sandboxes()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 5 of 6",
            header_text='"Prove it\'s safe" can freeze beneficial innovation.',
            examples=[
                (
                    "Strong precautionary principle:",
                    "Burden on the innovator to prove no harm before deployment.",
                ),
                (
                    "Electrification:",
                    "Would have failed a strong precautionary test. Changed the world.",
                ),
                (
                    "Penicillin:",
                    "Rushed to deployment in wartime. Saved millions. Approval came later.",
                ),
                (
                    "The honest question:",
                    "Which risks, at what scale, with what reversibility, are worth taking?",
                ),
            ],
            closing_text="The precautionary principle applies in both directions.",
        )

    def _rules_vs_standards(self) -> None:
        """Explain the rules vs. standards distinction visually."""
        header: Text = make_header("The False Binary — Rules vs. Standards")
        header.to_edge(UP, buff=0.55)
        self.play(Write(header), run_time=0.8)
        self.wait(0.2)

        # Two columns
        rule_title: Text = Text("Rule", font_size=22, color=RED_D, weight=BOLD)
        rule_title.move_to(LEFT * 3.5 + UP * 1.8)

        std_title: Text = Text("Standard", font_size=22, color=GREEN_D, weight=BOLD)
        std_title.move_to(RIGHT * 3.5 + UP * 1.8)

        divider: Line = Line(UP * 2.5, DOWN * 2.5, color=GRAY, stroke_width=1)

        rule_ex: Text = Text(
            '"You must show up\nfor work on time."',
            font_size=16,
            color=GRAY_B,
        )
        rule_ex.next_to(rule_title, DOWN, buff=0.3)

        std_ex: Text = Text(
            '"You must start work\nwithin 15 minutes\nof your shift beginning."',
            font_size=16,
            color=GRAY_B,
        )
        std_ex.next_to(std_title, DOWN, buff=0.3)

        rule_note: Text = Text(
            "Rigid.\nOne prescribed method.",
            font_size=14,
            color=ORANGE,
        )
        rule_note.next_to(rule_ex, DOWN, buff=0.4)

        std_note: Text = Text(
            "Flexible.\nMany ways to comply.\nRoom for ingenuity.",
            font_size=14,
            color=GREEN_B,
        )
        std_note.next_to(std_ex, DOWN, buff=0.4)

        self.play(Create(divider))
        self.play(FadeIn(rule_title), FadeIn(std_title))
        self.play(FadeIn(rule_ex), FadeIn(std_ex))
        self.play(FadeIn(rule_note), FadeIn(std_note))
        self.wait(1.5)

        insight: Text = Text(
            "Regulated and innovative are not opposites.\nStandards allow both simultaneously.",
            font_size=17,
            color=GOLD_D,
            slant=ITALIC,
        )
        insight.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(insight))
        self.wait(1.5)

        self.play(
            FadeOut(header),
            FadeOut(divider),
            FadeOut(rule_title),
            FadeOut(std_title),
            FadeOut(rule_ex),
            FadeOut(std_ex),
            FadeOut(rule_note),
            FadeOut(std_note),
            FadeOut(insight),
            run_time=0.7,
        )

    def _sandboxes(self) -> None:
        """Regulatory sandboxes explained."""
        header: Text = make_header("Regulatory Sandboxes")
        header.to_edge(UP, buff=0.55)
        self.play(Write(header), run_time=0.8)
        self.wait(0.2)

        points: list[tuple[str, str]] = [
            (
                "What it is:",
                "A controlled, lower-stakes version of the proposed regulatory environment.",
            ),
            (
                "How it works:",
                "New products operate in the sandbox before wider deployment.",
            ),
            (
                "What regulators learn:",
                "Unanticipated uses, risks, and benefits — before they affect millions.",
            ),
            (
                "What entities learn:",
                "How to comply effectively, where the rules need refinement.",
            ),
            (
                "The analogy:",
                "Clinical trials for pharmaceuticals. Not perfect — but better-informed.",
            ),
        ]

        example_mobs: list[VGroup] = [
            make_example_block(label, detail) for label, detail in points
        ]
        start_pos = header.get_bottom() + DOWN * 0.6 + LEFT * 5.5
        stacked: VGroup = stack_bullets(example_mobs, start=start_pos, spacing=0.6)

        for mob in example_mobs:
            self.play(FadeIn(mob, shift=RIGHT * 0.15), run_time=0.45)
            self.wait(0.35)

        closing: Text = make_closing(
            "Learn before you scale. The sandbox is not a loophole — it is a laboratory."
        )
        closing.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(closing, shift=UP * 0.1))
        self.wait(2.0)

        self.play(
            FadeOut(header),
            FadeOut(stacked),
            FadeOut(closing),
            run_time=0.7,
        )
