"""
scene_04_doubt3.py

Doubt 3 — Regulatory capture.
Response — Capture is an argument for better-designed regulation, not less.
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


class Doubt3Capture(Scene):
    """Doubt 3 — Regulatory capture."""

    def construct(self) -> None:
        self._doubt()
        self._response()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 3 of 6",
            header_text="Regulators end up serving the regulated, not the public.",
            examples=[
                (
                    "Revolving door:",
                    "Industry → regulator → industry. Allegiances follow careers.",
                ),
                (
                    "EU AI Act:",
                    "Shaped significantly by lobbying from the companies it was meant to govern.",
                ),
                (
                    "Responsible AI principles:",
                    "Written by the labs themselves. The regulated define the regulation.",
                ),
                (
                    "Social capture:",
                    "Same conferences, same circles, same ideological defaults.",
                ),
            ],
            closing_text="Capture is not a hypothetical risk. It is the current state.",
        )

    def _response(self) -> None:
        resp_header: Text = Text(
            "Response — Capture argues for better design, not less regulation.",
            font_size=26,
            color=GREEN_D,
            weight=BOLD,
        )
        resp_header.to_edge(UP, buff=0.55)
        self.play(Write(resp_header), run_time=0.9)
        self.wait(0.3)

        points: list[tuple[str, str]] = [
            (
                "Mandatory independent review:",
                "Assessments by bodies with no financial stake in the outcome.",
            ),
            (
                "Cooling-off periods:",
                "Prevent direct industry → regulator → industry movement.",
            ),
            (
                "Civil society funding:",
                "Public money for community groups to participate in regulatory processes.",
            ),
            (
                "Transparency requirements:",
                "Public disclosure of who shaped a regulation and how.",
            ),
            (
                "The principle:",
                "Capture happens when governance design allows it. Design against it.",
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
            "The problem is not that regulation exists. It is who controls it."
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
