"""
scene_07_doubt6.py

Doubt 6 — Regulations produce unintended consequences.
Response — Imperfect regulation vs. no regulation is still a choice.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from manim import *  # noqa: E402
from shared.lecture import (  # noqa: E402
    animate_doubt_scene,
    make_example_block,
    make_closing,
    stack_bullets,
)


class Doubt6Consequences(Scene):
    """Doubt 6 — Unintended regulatory consequences."""

    def construct(self) -> None:
        self._doubt()
        self._response()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 6 of 6",
            header_text="Regulations produce effects their designers didn't intend.",
            examples=[
                (
                    "EV mandates:",
                    "May keep lower-income people in older, more polluting cars longer.",
                ),
                (
                    "Strict AI regulation in one jurisdiction:",
                    "Pushes development to places with fewer protections. Worse globally.",
                ),
                (
                    "Compliance cost asymmetry:",
                    "Large incumbents absorb it. Small competitors cannot. Entrenchment.",
                ),
                (
                    "Backward-looking rules:",
                    "Respond to past harms. Miss the next form the harm takes.",
                ),
            ],
            closing_text="Regulations aren't magic. They can't enforce themselves perfectly.",
        )

    def _response(self) -> None:
        resp_header: Text = Text(
            "Response — Imperfect regulation vs. no regulation is still a choice.",
            font_size=25,
            color=GREEN_D,
            weight=BOLD,
        )
        resp_header.to_edge(UP, buff=0.55)
        self.play(Write(resp_header), run_time=0.9)
        self.wait(0.3)

        points: list[tuple[str, str]] = [
            (
                "The relevant comparison:",
                "Not 'regulation vs. no harm' — but 'regulation vs. harm without it'.",
            ),
            (
                "Precaution is bidirectional:",
                "Caution about acting. Equal caution about not acting.",
            ),
            (
                "Unintended consequences are a design problem:",
                "Pilot programmes. Monitoring requirements. Built-in revision cycles.",
            ),
            (
                "Standards over rules:",
                "Flexibility reduces the chance of rigid rules producing perverse outcomes.",
            ),
            (
                "The honest position:",
                "All policy has unintended effects. That is an argument for care, not inaction.",
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
            "Not acting is also a policy. It also has unintended consequences."
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
