from manim import *
import numpy as np

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
PARADIGM_COLOR: ManimColor = BLUE_D
CRITIQUE_CONCEPT_COLOR: ManimColor = ORANGE
CRITIQUE_CAPITAL_COLOR: ManimColor = RED_D
CRITIQUE_ANTHRO_COLOR: ManimColor = GREEN_D
CASE_STUDY_COLOR: ManimColor = TEAL_D
DUNE_COLOR: ManimColor = GOLD_D
REFRAME_COLOR: ManimColor = PURPLE_B


# ---------------------------------------------------------------------------
# Helpers (same pattern as 02_intelligence)
# ---------------------------------------------------------------------------
def make_cluster(
    title: str,
    items: list[str],
    color: ManimColor,
    position: np.ndarray,
    title_font: int = 16,
    item_font: int = 12,
) -> VGroup:
    """Return a labelled cluster box centred at *position*.

    VGroup structure: [RoundedRectangle, VGroup[title_text, items_group]]
    Access box via group[0] for boundary-point edge routing.
    """
    title_mob: Text = Text(title, font_size=title_font, color=color, weight=BOLD)
    item_mobs: list[Text] = [
        Text(f"- {item}", font_size=item_font, color=WHITE) for item in items
    ]
    items_group: VGroup = VGroup(*item_mobs).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    items_group.next_to(title_mob, DOWN, buff=0.1, aligned_edge=LEFT)

    content: VGroup = VGroup(title_mob, items_group)
    box: RoundedRectangle = RoundedRectangle(
        corner_radius=0.2,
        width=content.width + 0.5,
        height=content.height + 0.35,
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
    opacity: float = 0.55,
) -> Arrow:
    """Return an Arrow from the boundary of *source* to the boundary of *target*."""
    direction: np.ndarray = normalize(target.get_center() - source.get_center())
    start: np.ndarray = source[0].get_boundary_point(direction)
    end: np.ndarray = target[0].get_boundary_point(-direction)
    return Arrow(
        start=start,
        end=end,
        buff=0.08,
        color=color,
        stroke_opacity=opacity,
        stroke_width=1.8,
        tip_length=0.16,
        max_tip_length_to_length_ratio=0.25,
    )


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
class NarrowAIvsAGI(Scene):
    """Animated concept map for 'Narrow AI vs. AGI' — Foundation of Responsible AI.

    Three-act structure:
      Act I   — The AI paradigm landscape
      Act II  — Three critiques of AGI as a goal
      Act III — The Dune lens and the reframed question
    """

    def construct(self) -> None:
        self._show_title()

        clusters: dict[str, VGroup] = self._build_clusters()

        self._act_one(clusters)
        self._act_two(clusters)
        self._act_three(clusters)

        self.wait(2)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    def _show_title(self) -> None:
        heading: Text = Text("Narrow AI vs. AGI", font_size=42)
        sub: Text = Text(
            "Paradigms, Critiques, and the Reframed Question",
            font_size=18,
            color=GRAY,
        )
        sub.next_to(heading, DOWN, buff=0.2)
        group: VGroup = VGroup(heading, sub)

        self.play(Write(heading), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.1))
        self.wait(0.8)
        self.play(group.animate.scale(0.4).to_corner(UL, buff=0.22))

    # ------------------------------------------------------------------
    # Cluster definitions
    # ------------------------------------------------------------------
    def _build_clusters(self) -> dict[str, VGroup]:
        return {
            # --- Act I: Paradigms (top row) ---
            "narrow": make_cluster(
                "Narrow AI",
                ["Task-specific", "Chess, spam filters, classifiers"],
                PARADIGM_COLOR,
                np.array([-5.2, 2.8, 0]),
            ),
            "agi": make_cluster(
                "AGI",
                ["General-purpose", "No agreed definition", "Contested goal"],
                PARADIGM_COLOR,
                np.array([0.0, 2.8, 0]),
            ),
            "symbolic": make_cluster(
                "Symbolic AI",
                ["Rules + logic", "Interpretable", "Brittle at edges"],
                PARADIGM_COLOR,
                np.array([-5.2, 1.0, 0]),
            ),
            "neural": make_cluster(
                "Neural / Connectionist",
                ["Learned from data", "Deep learning"],
                PARADIGM_COLOR,
                np.array([5.2, 1.0, 0]),
            ),
            "generative": make_cluster(
                "Generative Models",
                ["Claude, ChatGPT, Midjourney", "Subcategory of AI, not AI itself"],
                PARADIGM_COLOR,
                np.array([5.2, 2.8, 0]),
            ),
            # --- Act II: Three critiques (middle row) ---
            "critique_concept": make_cluster(
                "Critique I - Conceptual",
                ["Category error?", "No agreed definition", "Narrative, not target"],
                CRITIQUE_CONCEPT_COLOR,
                np.array([-5.2, -0.9, 0]),
            ),
            "critique_capital": make_cluster(
                "Critique II - Economic",
                [
                    "Capital concentration",
                    "Underconsumption problem",
                    "UBI: gestured at, not designed",
                    "Regulatory capture",
                ],
                CRITIQUE_CAPITAL_COLOR,
                np.array([0.0, -0.9, 0]),
            ),
            "critique_anthro": make_cluster(
                "Critique III - Anthropological",
                [
                    "Hedonic treadmill",
                    "Flow states (Csikszentmihalyi)",
                    "Antifragility (Taleb)",
                    "Meaning requires difficulty (Frankl)",
                ],
                CRITIQUE_ANTHRO_COLOR,
                np.array([5.2, -0.9, 0]),
            ),
            # --- Act II cont: Case study (bridges economic + anthropological) ---
            "ksa": make_cluster(
                "Case Study - Disconnected from Struggle",
                [
                    "Resource-rent insulated citizens from work",
                    "Productive economy outsourced entirely",
                    "Culture suspended, not preserved",
                    "Binary: tradition vs. imported modernity",
                    "Youth are victims of the policy, not the problem",
                ],
                CASE_STUDY_COLOR,
                np.array([0.0, -2.2, 0]),
            ),
            # --- Act III: Dune + Reframe (bottom row) ---
            "dune": make_cluster(
                "The Dune Lens",
                [
                    "Butlerian Jihad - atrophy, not malice",
                    "Mentats - cultivate human cognition",
                    "Spice = Compute (controlled dependency)",
                    "Fremen - constraint as strength",
                ],
                DUNE_COLOR,
                np.array([-3.2, -2.9, 0]),
            ),
            "reframe": make_cluster(
                "The Reframed Question",
                [
                    "Which difficulty is worth preserving?",
                    "Which suffering is unnecessary?",
                    "Who decides?",
                ],
                REFRAME_COLOR,
                np.array([3.2, -2.9, 0]),
            ),
        }

    # ------------------------------------------------------------------
    # Act I — Paradigm landscape
    # ------------------------------------------------------------------
    def _act_one(self, clusters: dict[str, VGroup]) -> None:
        act_label: Text = Text("Act I  -  The Landscape", font_size=14, color=GRAY)
        act_label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(act_label))

        paradigm_keys: list[str] = ["narrow", "symbolic", "neural", "generative", "agi"]
        for key in paradigm_keys:
            self.play(FadeIn(clusters[key], shift=UP * 0.08), run_time=0.55)

        # Edges within paradigms
        paradigm_edges: list[tuple[str, str, ManimColor]] = [
            ("symbolic", "narrow", PARADIGM_COLOR),
            ("neural", "generative", PARADIGM_COLOR),
            ("narrow", "agi", PARADIGM_COLOR),
            ("generative", "agi", PARADIGM_COLOR),
        ]
        for src, tgt, color in paradigm_edges:
            self.play(
                Create(make_edge(clusters[src], clusters[tgt], color=color)),
                run_time=0.4,
            )

        self.wait(0.6)
        self.play(FadeOut(act_label))

    # ------------------------------------------------------------------
    # Act II — Three critiques
    # ------------------------------------------------------------------
    def _act_two(self, clusters: dict[str, VGroup]) -> None:
        act_label: Text = Text(
            "Act II  -  Three Critiques of AGI", font_size=14, color=GRAY
        )
        act_label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(act_label))

        critique_keys: list[str] = [
            "critique_concept",
            "critique_capital",
            "critique_anthro",
        ]
        critique_colors: list[ManimColor] = [
            CRITIQUE_CONCEPT_COLOR,
            CRITIQUE_CAPITAL_COLOR,
            CRITIQUE_ANTHRO_COLOR,
        ]
        for key, color in zip(critique_keys, critique_colors):
            self.play(GrowFromCenter(clusters[key]), run_time=0.8)
            edge: Arrow = make_edge(
                clusters["agi"], clusters[key], color=color, opacity=0.7
            )
            self.play(Create(edge), run_time=0.4)

        # Case study emerges from the economic + anthropological critiques
        self.wait(0.3)
        self.play(FadeIn(clusters["ksa"], shift=DOWN * 0.15), run_time=0.9)
        ksa_edges: list[tuple[str, str]] = [
            ("critique_capital", "ksa"),
            ("critique_anthro", "ksa"),
        ]
        for src, tgt in ksa_edges:
            self.play(
                Create(
                    make_edge(
                        clusters[src],
                        clusters[tgt],
                        color=CASE_STUDY_COLOR,
                        opacity=0.7,
                    )
                ),
                run_time=0.4,
            )

        self.wait(0.6)
        self.play(FadeOut(act_label))

    # ------------------------------------------------------------------
    # Act III — Dune lens + reframed question
    # ------------------------------------------------------------------
    def _act_three(self, clusters: dict[str, VGroup]) -> None:
        act_label: Text = Text(
            "Act III  -  The Dune Lens and the Real Question", font_size=14, color=GRAY
        )
        act_label.to_edge(RIGHT, buff=0.3).shift(UP * 3.5)
        self.play(FadeIn(act_label))

        # Dune cluster rises from below
        self.play(FadeIn(clusters["dune"], shift=UP * 0.2), run_time=0.8)

        dune_edges: list[tuple[str, str, ManimColor]] = [
            ("critique_capital", "dune", DUNE_COLOR),
            ("critique_anthro", "dune", DUNE_COLOR),
        ]
        for src, tgt, color in dune_edges:
            self.play(
                Create(make_edge(clusters[src], clusters[tgt], color=color)),
                run_time=0.4,
            )

        self.wait(0.3)

        # Reframed question emerges from all three critiques converging
        self.play(GrowFromCenter(clusters["reframe"]), run_time=1.0)

        reframe_edges: list[tuple[str, str, ManimColor]] = [
            ("critique_concept", "reframe", REFRAME_COLOR),
            ("critique_capital", "reframe", REFRAME_COLOR),
            ("critique_anthro", "reframe", REFRAME_COLOR),
            ("ksa", "reframe", REFRAME_COLOR),
            ("dune", "reframe", REFRAME_COLOR),
        ]
        for src, tgt, color in reframe_edges:
            self.play(
                Create(make_edge(clusters[src], clusters[tgt], color=color)),
                run_time=0.35,
            )

        self.wait(0.4)

        # Final pulse on the reframed question
        self.play(Indicate(clusters["reframe"], color=REFRAME_COLOR, scale_factor=1.06))

        closing: Text = Text(
            "The race concentrates power. The real question redistributes it.",
            font_size=13,
            color=REFRAME_COLOR,
        )
        closing.next_to(clusters["reframe"], DOWN, buff=0.25)
        self.play(FadeIn(closing))

        self.wait(1.5)
        self.play(FadeOut(act_label))
