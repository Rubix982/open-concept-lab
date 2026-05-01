"""
scene_01_lessig.py

The Lessig Four — Architecture, Market, Norms, Law —
four forces that regulate behaviour in any system simultaneously.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from manim import *  # noqa: E402
import numpy as np  # noqa: E402

# ---------------------------------------------------------------------------
# Colours per force
# ---------------------------------------------------------------------------
ARCH_COLOR: ManimColor = BLUE_D
MARKET_COLOR: ManimColor = GREEN_D
NORMS_COLOR: ManimColor = GOLD_D
LAW_COLOR: ManimColor = RED_D
HUB_COLOR: ManimColor = WHITE


def make_force_node(
    label: str,
    sublabel: str,
    color: ManimColor,
    position: np.ndarray,
) -> VGroup:
    """Circular node with label and sublabel."""
    circle: Circle = Circle(
        radius=0.9, color=color, fill_color=color, fill_opacity=0.15, stroke_width=2
    )
    circle.move_to(position)

    lbl: Text = Text(label, font_size=18, color=color, weight=BOLD)
    lbl.move_to(position + UP * 0.18)

    sub: Text = Text(sublabel, font_size=11, color=GRAY_B)
    sub.move_to(position + DOWN * 0.22)

    return VGroup(circle, lbl, sub)


class LessigFour(Scene):
    """The four regulatory forces — Lessig framework."""

    def construct(self) -> None:
        self._intro()
        forces, hub, arrows = self._build()
        self._animate(forces, hub, arrows)
        self._ai_applications(forces)
        self.wait(2)

    def _intro(self) -> None:
        intro: Text = Text(
            "Law is only one of four forces that regulate behaviour.",
            font_size=24,
            color=WHITE,
        )
        self.play(Write(intro), run_time=1.0)
        self.wait(1.2)
        self.play(FadeOut(intro))

    def _build(self) -> tuple[dict[str, VGroup], VGroup, list[Arrow]]:
        # Hub
        hub_circle: Circle = Circle(
            radius=0.7,
            color=HUB_COLOR,
            fill_color=GRAY_E,
            fill_opacity=0.8,
            stroke_width=2,
        )
        hub_label: Text = Text("Behaviour", font_size=16, color=WHITE, weight=BOLD)
        hub: VGroup = VGroup(hub_circle, hub_label)
        hub.move_to(ORIGIN)

        # Four force nodes at compass points
        forces: dict[str, VGroup] = {
            "arch": make_force_node(
                "Architecture", "what the system\nmakes possible", ARCH_COLOR, UP * 2.6
            ),
            "market": make_force_node(
                "Market", "price signals\nand incentives", MARKET_COLOR, RIGHT * 4.2
            ),
            "norms": make_force_node(
                "Norms", "social pressure\nand expectations", NORMS_COLOR, DOWN * 2.6
            ),
            "law": make_force_node(
                "Law", "what the state\npermits or prohibits", LAW_COLOR, LEFT * 4.2
            ),
        }

        # Arrows from each force to hub
        arrows: list[Arrow] = []
        for force in forces.values():
            direction: np.ndarray = normalize(hub.get_center() - force.get_center())
            start: np.ndarray = force[0].get_boundary_point(direction)
            end: np.ndarray = hub_circle.get_boundary_point(-direction)
            arrows.append(
                Arrow(
                    start=start,
                    end=end,
                    buff=0.08,
                    stroke_width=1.8,
                    tip_length=0.16,
                    color=GRAY,
                )
            )

        return forces, hub, arrows

    def _animate(
        self,
        forces: dict[str, VGroup],
        hub: VGroup,
        arrows: list[Arrow],
    ) -> None:
        # Hub appears first
        self.play(GrowFromCenter(hub), run_time=0.8)
        self.wait(0.2)

        # Forces appear in order with their arrows
        order: list[str] = ["arch", "market", "norms", "law"]
        for key, arrow in zip(order, arrows):
            self.play(
                FadeIn(
                    forces[key],
                    shift=normalize(ORIGIN - forces[key].get_center()) * 0.2,
                ),
                run_time=0.6,
            )
            self.play(Create(arrow), run_time=0.4)

        self.wait(0.5)

    def _ai_applications(self, forces: dict[str, VGroup]) -> None:
        """Fade in AI application label beneath each force node."""
        applications: dict[str, str] = {
            "arch": "model design, defaults,\nwhat users can/cannot do",
            "market": "business models, compute costs,\nwho can afford what",
            "norms": "professional ethics,\npublic opinion, reputation",
            "law": "GDPR, EU AI Act,\nliability frameworks",
        }

        label: Text = Text(
            "Applied to AI:",
            font_size=18,
            color=GRAY,
        )
        label.to_edge(DOWN, buff=1.2)
        self.play(FadeIn(label))

        for key, text in applications.items():
            force: VGroup = forces[key]
            app: Text = Text(text, font_size=10, color=GRAY_B)
            app.next_to(force, DOWN, buff=0.15)
            self.play(FadeIn(app, shift=UP * 0.08), run_time=0.45)

        self.wait(1.0)

        closing: Text = Text(
            "Law alone — without Architecture, Market, and Norms — produces compliance theatre.",  # noqa: E501
            font_size=16,
            color=GOLD_D,
            slant=ITALIC,
        )
        closing.to_edge(DOWN, buff=0.3)
        self.play(
            FadeOut(label),
            FadeIn(closing),
        )
        self.wait(2.0)
