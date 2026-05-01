from manim import *
import numpy as np

# ---------------------------------------------------------------------------
# Colour palette — one per cluster
# ---------------------------------------------------------------------------
DEF_COLOR: ManimColor = BLUE_D
LEARN_COLOR: ManimColor = GREEN_D
TEACH_COLOR: ManimColor = GOLD_D
TOM_COLOR: ManimColor = PURPLE_B
AI_COLOR: ManimColor = RED_D


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_cluster(
    title: str,
    items: list[str],
    color: ManimColor,
    position: np.ndarray,
    title_font: int = 17,
    item_font: int = 13,
) -> VGroup:
    """Return a labelled, colour-coded cluster box centred at *position*.

    Structure: VGroup[RoundedRectangle, VGroup[title_text, items_group]]
    Callers can access the box as group[0] for boundary-point calculations.
    """
    title_mob: Text = Text(title, font_size=title_font, color=color, weight=BOLD)
    item_mobs: list[Text] = [
        Text(f"- {item}", font_size=item_font, color=WHITE) for item in items
    ]
    items_group: VGroup = VGroup(*item_mobs).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    items_group.next_to(title_mob, DOWN, buff=0.12, aligned_edge=LEFT)

    content: VGroup = VGroup(title_mob, items_group)

    box: RoundedRectangle = RoundedRectangle(
        corner_radius=0.2,
        width=content.width + 0.5,
        height=content.height + 0.4,
        color=color,
        fill_color=color,
        fill_opacity=0.12,
        stroke_width=2,
    )
    box.move_to(content.get_center())

    group: VGroup = VGroup(box, content)
    group.move_to(position)
    return group


def make_edge(
    source: VGroup,
    target: VGroup,
    color: ManimColor = WHITE,
    opacity: float = 0.6,
) -> Arrow:
    """Return an Arrow from the boundary of *source* to the boundary of *target*.

    Uses get_boundary_point so arrows terminate at box edges, not centres.
    """
    direction: np.ndarray = normalize(target.get_center() - source.get_center())
    start: np.ndarray = source[0].get_boundary_point(direction)
    end: np.ndarray = target[0].get_boundary_point(-direction)
    return Arrow(
        start=start,
        end=end,
        buff=0.08,
        color=color,
        stroke_opacity=opacity,
        stroke_width=2,
        tip_length=0.18,
        max_tip_length_to_length_ratio=0.25,
    )


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
class IntelligenceConceptMap(Scene):
    """Animated concept map for 'What is Intelligence?' — Foundation of Responsible AI."""

    def construct(self) -> None:
        self._show_title()
        clusters: dict[str, VGroup] = self._build_clusters()
        self._animate_clusters(clusters)
        self._animate_edges(clusters)
        self._highlight_hub(clusters["teach"])
        self.wait(2)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    def _show_title(self) -> None:
        heading: Text = Text("What is Intelligence?", font_size=42)
        sub: Text = Text("Concept Map  -  Foundation of Responsible AI", font_size=20, color=GRAY)
        sub.next_to(heading, DOWN, buff=0.2)
        group: VGroup = VGroup(heading, sub)

        self.play(Write(heading), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.1))
        self.wait(0.8)
        self.play(group.animate.scale(0.42).to_corner(UL, buff=0.25))

    # ------------------------------------------------------------------
    # Cluster definitions
    # ------------------------------------------------------------------
    def _build_clusters(self) -> dict[str, VGroup]:
        return {
            "def": make_cluster(
                "Definitions of Intelligence",
                ["Behavioral  (Turing)", "Metaphysical", "Functional / Adaptive"],
                DEF_COLOR,
                np.array([-4.8, 2.2, 0]),
            ),
            "learn": make_cluster(
                "Learning Philosophies",
                [
                    "Piaget - Constructivism",
                    "Vygotsky - ZPD",
                    "Siemens - Connectivism",
                ],
                LEARN_COLOR,
                np.array([-4.8, -2.0, 0]),
            ),
            "teach": make_cluster(
                "Teaching & Transmission",
                [
                    "Teaching Criterion  (hub)",
                    "Socratic Method",
                    "Feynman Technique",
                    "Bloom's Taxonomy",
                    "Scaffolding",
                ],
                TEACH_COLOR,
                np.array([0.2, 0.1, 0]),
            ),
            "tom": make_cluster(
                "Theory of Mind",
                ["Metacognition", "Gap-Sensing", "Theory of Mind", "Self-Awareness"],
                TOM_COLOR,
                np.array([4.8, 2.2, 0]),
            ),
            "ai": make_cluster(
                "AI Systems",
                [
                    "Intelligent Tutoring",
                    "Knowledge Graphs",
                    "Adaptive Learning",
                    "LLMs",
                ],
                AI_COLOR,
                np.array([4.8, -2.0, 0]),
            ),
        }

    # ------------------------------------------------------------------
    # Animations
    # ------------------------------------------------------------------
    def _animate_clusters(self, clusters: dict[str, VGroup]) -> None:
        # Outer clusters fade in first
        outer: list[str] = ["def", "learn", "tom", "ai"]
        for key in outer:
            self.play(FadeIn(clusters[key], shift=UP * 0.1), run_time=0.65)

        self.wait(0.4)

        # Teaching hub grows from centre — emphasises its role
        self.play(GrowFromCenter(clusters["teach"]), run_time=1.1)
        self.wait(0.5)

    def _animate_edges(self, clusters: dict[str, VGroup]) -> None:
        # (source, target, colour) — drawn in narrative order
        connections: list[tuple[str, str, ManimColor]] = [
            # Definitions feed into Teaching
            ("def", "teach", DEF_COLOR),
            # Learning philosophies ground both Definitions and Teaching
            ("learn", "def", LEARN_COLOR),
            ("learn", "teach", LEARN_COLOR),
            # Theory of Mind powers Teaching and AI
            ("tom", "teach", TOM_COLOR),
            ("tom", "ai", TOM_COLOR),
            # Teaching drives AI applications
            ("teach", "ai", TEACH_COLOR),
            # Connectivism feeds Knowledge Graphs in AI
            ("learn", "ai", LEARN_COLOR),
        ]
        for src, tgt, color in connections:
            edge: Arrow = make_edge(
                clusters[src], clusters[tgt], color=color, opacity=0.65
            )
            self.play(Create(edge), run_time=0.5)

        self.wait(0.5)

    def _highlight_hub(self, hub: VGroup) -> None:
        """Pulse the hub cluster and surface the key insight."""
        self.play(Indicate(hub, color=GOLD_D, scale_factor=1.06), run_time=1.0)

        label: Text = Text(
            "Teaching Criterion - the node that connects all clusters",
            font_size=13,
            color=GOLD_D,
        )
        label.next_to(hub, DOWN, buff=0.3)
        self.play(FadeIn(label))
        self.wait(1.5)
