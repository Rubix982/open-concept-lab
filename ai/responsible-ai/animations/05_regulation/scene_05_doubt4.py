"""
scene_05_doubt4.py

Doubt 4 — Regulators can't foresee what they're regulating against.
Response — AI's harms are not speculative. They are visible now.
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


class Doubt4Foresight(Scene):
    """Doubt 4 — Technosocial opacity and the Collingridge Dilemma."""

    def construct(self) -> None:
        self._doubt()
        self._collingridge()
        self._response()
        self.wait(1.5)

    def _doubt(self) -> None:
        animate_doubt_scene(
            scene=self,
            counter_text="Doubt 4 of 6",
            header_text="Regulators can't foresee what they're regulating against.",
            examples=[
                (
                    "Technosocial opacity (Shannon Vallor):",
                    "Medium and long-term effects of novel technology are unknowable in advance.",
                ),
                (
                    "Historical pattern:",
                    "Every technology simultaneously over- and under-estimated in its effects.",
                ),
                (
                    "Social media:",
                    "Regulated a decade after documented harm. By then: deeply embedded.",
                ),
                (
                    "The dilemma:",
                    "Regulate too early = uninformed. Regulate too late = can't change course.",
                ),
            ],
            closing_text="You are always choosing between regulating in ignorance or regulating too late.",
        )

    def _collingridge(self) -> None:
        """Visualise the Collingridge Dilemma as a timeline."""
        title: Text = Text(
            "The Collingridge Dilemma",
            font_size=28,
            color=BLUE_D,
            weight=BOLD,
        )
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=0.8)

        # Timeline arrow
        arrow: Arrow = Arrow(
            start=LEFT * 5.5,
            end=RIGHT * 5.5,
            color=GRAY,
            stroke_width=2,
            tip_length=0.2,
        )
        arrow.move_to(ORIGIN)
        self.play(Create(arrow), run_time=0.7)

        # Labels on timeline
        early: Text = Text("Too Early", font_size=16, color=ORANGE)
        early.next_to(arrow.get_left(), UP, buff=0.3)

        late: Text = Text("Too Late", font_size=16, color=RED_D)
        late.next_to(arrow.get_right(), UP, buff=0.3)

        now: Text = Text("AI — Right Now", font_size=16, color=GOLD_D, weight=BOLD)
        now_dot: Dot = Dot(color=GOLD_D, radius=0.12)
        now_dot.move_to(arrow.point_from_proportion(0.55))
        now.next_to(now_dot, UP, buff=0.2)

        early_desc: Text = Text(
            "Effects unknown\nRegulation hard to design",
            font_size=13,
            color=GRAY_B,
        )
        early_desc.next_to(early, DOWN, buff=0.3)

        late_desc: Text = Text(
            "Effects known\nToo embedded to change",
            font_size=13,
            color=GRAY_B,
        )
        late_desc.next_to(late, DOWN, buff=0.3)

        self.play(FadeIn(early), FadeIn(early_desc))
        self.wait(0.4)
        self.play(FadeIn(late), FadeIn(late_desc))
        self.wait(0.4)
        self.play(GrowFromCenter(now_dot), FadeIn(now))
        self.wait(1.5)

        self.play(
            FadeOut(title),
            FadeOut(arrow),
            FadeOut(early),
            FadeOut(early_desc),
            FadeOut(late),
            FadeOut(late_desc),
            FadeOut(now_dot),
            FadeOut(now),
            run_time=0.6,
        )

    def _response(self) -> None:
        resp_header: Text = Text(
            "Response — AI's harms are not speculative. They are visible now.",
            font_size=26,
            color=GREEN_D,
            weight=BOLD,
        )
        resp_header.to_edge(UP, buff=0.55)
        self.play(Write(resp_header), run_time=0.9)
        self.wait(0.3)

        points: list[tuple[str, str]] = [
            (
                "Job automation:",
                "Happening now. Creates different work, eliminates other work.",
            ),
            (
                "Algorithmic discrimination:",
                "Documented in hiring, credit, healthcare, criminal justice.",
            ),
            (
                "Privacy erosion:",
                "Inferences from vast data already challenging protections.",
            ),
            (
                "Environmental cost:",
                "Data centre energy and water use escalating now, not hypothetically.",
            ),
            (
                "Existing law already covers many of these.",
                "Start there. Apply what works. Extend where gaps exist.",
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
            "Waiting for certainty is also a choice — with consequences."
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
