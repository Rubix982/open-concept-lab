"""
three_waves_of_ai.py

Animated version of Xu's three-wave AI development table.
Part of the Human-Centered AI series (Module 08).

Each wave materialises progressively — technology first, then human needs,
then focus, then characteristics. The third wave is held longest to land
the HCAI point.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # noqa: E402

from manim import *  # noqa: E402

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
WAVE1_COLOR: ManimColor = GRAY_D
WAVE2_COLOR: ManimColor = BLUE_D
WAVE3_COLOR: ManimColor = TEAL_D
LABEL_COLOR: ManimColor = WHITE
DIM_COLOR: ManimColor = GRAY_B
HIGHLIGHT_COLOR: ManimColor = GOLD_D


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
ROWS: list[str] = [
    "Major advances\nin technologies",
    "Human needs",
    "Focus",
    "Characteristics",
]

WAVE1: list[str] = [
    "Symbolism, connectionism,\nproduction systems,\nknowledge inference,\nexpert systems",
    "Not satisfied",
    "Technological solutions",
    "Academia driven",
]

WAVE2: list[str] = [
    "Statistical models, speech\nrecognition, neural networks\nin pattern recognition,\nexpert systems",
    "Not satisfied",
    "Technological solutions",
    "Academia driven",
]

WAVE3: list[str] = [
    "Deep learning breakthroughs:\nspeech recognition, pattern\nrecognition, big data,\nhigh-performance compute",
    "Starting to provide useful\nand real problem-solving\nAI solutions",
    "Integrated solutions:\nethical design +\ntechnological enhancement +\nhuman factors design",
    "Technological enhancement\nand application +\na human-centered approach",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_cell(
    text: str,
    width: float,
    height: float,
    color: ManimColor,
    font_size: int = 13,
    is_header: bool = False,
) -> VGroup:
    """Single table cell — coloured border + text."""
    rect: Rectangle = Rectangle(
        width=width,
        height=height,
        color=color,
        fill_color=color,
        fill_opacity=0.12 if not is_header else 0.25,
        stroke_width=1.5,
    )
    txt: Text = Text(
        text,
        font_size=font_size,
        color=WHITE if is_header else DIM_COLOR,
        weight=BOLD if is_header else NORMAL,
    )
    txt.move_to(rect.get_center())
    # Scale down text if it overflows
    if txt.width > width - 0.2:
        txt.scale((width - 0.2) / txt.width)
    if txt.height > height - 0.1:
        txt.scale((height - 0.1) / txt.height)
    return VGroup(rect, txt)


def make_row_label(text: str, height: float) -> VGroup:
    """Left-side row label cell."""
    rect: Rectangle = Rectangle(
        width=2.2,
        height=height,
        color=GRAY,
        fill_color=GRAY,
        fill_opacity=0.1,
        stroke_width=1,
    )
    txt: Text = Text(text, font_size=12, color=LABEL_COLOR, weight=BOLD)
    txt.move_to(rect.get_center())
    if txt.width > 2.0:
        txt.scale(2.0 / txt.width)
    if txt.height > height - 0.1:
        txt.scale((height - 0.1) / txt.height)
    return VGroup(rect, txt)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
class ThreeWavesOfAI(Scene):
    """Xu's three-wave AI history table — animated progression."""

    CELL_W: float = 3.4
    CELL_H: float = 1.35
    LABEL_W: float = 2.2

    def construct(self) -> None:
        self._title()
        self._build_and_animate_table()
        self._closing()
        self.wait(2)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    def _title(self) -> None:
        title: Text = Text("Three Waves of AI", font_size=40, color=WHITE)
        sub: Text = Text(
            "Why the first two failed — and what the third requires",
            font_size=18,
            color=GRAY,
        )
        sub.next_to(title, DOWN, buff=0.25)
        group: VGroup = VGroup(title, sub)

        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub, shift=UP * 0.1))
        self.wait(0.8)
        self.play(group.animate.scale(0.38).to_corner(UL, buff=0.22))

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------
    def _build_and_animate_table(self) -> None:
        n_rows: int = len(ROWS)
        total_w: float = self.LABEL_W + self.CELL_W * 3
        total_h: float = self.CELL_H * n_rows + self.CELL_H  # +1 for header

        # Starting position — centre the table
        origin_x: float = -total_w / 2
        origin_y: float = total_h / 2 - self.CELL_H / 2 - 0.3

        # --- Header row ---
        headers: list[tuple[str, ManimColor]] = [
            ("First Wave\n(1950s–1970s)", WAVE1_COLOR),
            ("Second Wave\n(1980s–1990s)", WAVE2_COLOR),
            ("Third Wave\n(2006–)", WAVE3_COLOR),
        ]

        header_cells: list[VGroup] = []
        # blank top-left corner
        corner: Rectangle = Rectangle(
            width=self.LABEL_W,
            height=self.CELL_H,
            color=GRAY,
            fill_color=GRAY,
            fill_opacity=0.05,
            stroke_width=1,
        )
        corner.move_to(np.array([origin_x + self.LABEL_W / 2, origin_y, 0]))

        for i, (text, color) in enumerate(headers):
            cell: VGroup = make_cell(
                text,
                self.CELL_W,
                self.CELL_H,
                color,
                font_size=14,
                is_header=True,
            )
            x: float = origin_x + self.LABEL_W + self.CELL_W * i + self.CELL_W / 2
            cell.move_to(np.array([x, origin_y, 0]))
            header_cells.append(cell)

        self.play(FadeIn(corner), run_time=0.3)
        for cell in header_cells:
            self.play(FadeIn(cell, shift=DOWN * 0.1), run_time=0.4)
        self.wait(0.3)

        # --- Data rows — animate one row at a time ---
        all_row_labels: list[VGroup] = []
        all_wave1_cells: list[VGroup] = []
        all_wave2_cells: list[VGroup] = []
        all_wave3_cells: list[VGroup] = []

        for row_idx, (row_label, w1, w2, w3) in enumerate(
            zip(ROWS, WAVE1, WAVE2, WAVE3)
        ):
            y: float = origin_y - self.CELL_H * (row_idx + 1)

            label_mob: VGroup = make_row_label(row_label, self.CELL_H)
            label_mob.move_to(np.array([origin_x + self.LABEL_W / 2, y, 0]))

            c1: VGroup = make_cell(w1, self.CELL_W, self.CELL_H, WAVE1_COLOR)
            c1.move_to(np.array([origin_x + self.LABEL_W + self.CELL_W / 2, y, 0]))

            c2: VGroup = make_cell(w2, self.CELL_W, self.CELL_H, WAVE2_COLOR)
            c2.move_to(np.array([origin_x + self.LABEL_W + self.CELL_W * 1.5, y, 0]))

            c3: VGroup = make_cell(w3, self.CELL_W, self.CELL_H, WAVE3_COLOR)
            c3.move_to(np.array([origin_x + self.LABEL_W + self.CELL_W * 2.5, y, 0]))

            all_row_labels.append(label_mob)
            all_wave1_cells.append(c1)
            all_wave2_cells.append(c2)
            all_wave3_cells.append(c3)

            # Animate this row
            self.play(
                FadeIn(label_mob),
                FadeIn(c1, shift=RIGHT * 0.1),
                FadeIn(c2, shift=RIGHT * 0.1),
                FadeIn(c3, shift=RIGHT * 0.1),
                run_time=0.55,
            )

            # Pause on "Human needs" row to let it land
            if row_label == "Human needs":
                self.wait(0.8)
                # Highlight the two "Not satisfied" cells
                for cell in [c1, c2]:
                    self.play(
                        cell[0].animate.set_fill(RED_D, opacity=0.25),
                        run_time=0.4,
                    )
                self.wait(0.6)

        self.wait(0.8)

        # --- Highlight Wave 3 column ---
        highlight_label: Text = Text(
            "Third wave: first to ask what humans actually need",
            font_size=14,
            color=HIGHLIGHT_COLOR,
            slant=ITALIC,
        )
        highlight_label.to_edge(DOWN, buff=0.4)

        for cell in all_wave3_cells:
            self.play(
                cell[0].animate.set_fill(TEAL_D, opacity=0.3),
                run_time=0.3,
            )
        self.play(FadeIn(highlight_label))
        self.wait(2.0)
        self.play(FadeOut(highlight_label))

    # ------------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------------
    def _closing(self) -> None:
        closing: Text = Text(
            "The first two waves failed because they never asked what humans needed.\n"
            "The third wave asks — but the asking is still dominated by engineers.",
            font_size=16,
            color=GOLD_D,
            slant=ITALIC,
        )
        closing.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(closing))
        self.wait(2.5)
        self.play(FadeOut(closing))
