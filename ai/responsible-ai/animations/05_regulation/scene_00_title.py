"""
scene_00_title.py

Title card for the regulation lecture series.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from manim import *  # noqa: E402
from shared.lecture import make_title_card  # noqa: E402


class TitleCard(Scene):
    """Opening title card — Why Regulation?"""

    def construct(self) -> None:
        card: VGroup = make_title_card(
            title="Why Regulation?",
            subtitle="Six Doubts Worth Taking Seriously",
        )
        card.move_to(ORIGIN)

        self.play(Write(card[0]), run_time=1.2)
        self.play(FadeIn(card[1], shift=UP * 0.1))
        self.wait(1.5)

        # Transition line
        line: Line = Line(LEFT * 4, RIGHT * 4, color=BLUE_D, stroke_width=1.5)
        line.next_to(card[1], DOWN, buff=0.4)
        self.play(Create(line), run_time=0.6)

        tag: Text = Text(
            "Regulation shapes what is possible — not just what is permitted.",
            font_size=17,
            color=GRAY,
        )
        tag.next_to(line, DOWN, buff=0.3)
        self.play(FadeIn(tag))
        self.wait(2.0)

        self.play(FadeOut(VGroup(card, line, tag)))
        self.wait(0.3)
