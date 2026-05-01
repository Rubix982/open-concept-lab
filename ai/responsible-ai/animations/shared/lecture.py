"""
shared/lecture.py

Reusable primitives for lecture-style Manim animations.
Used across 05_regulation and future topic animations.
"""

from manim import *
import numpy as np

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
HEADER_COLOR: ManimColor = BLUE_D
EXAMPLE_COLOR: ManimColor = WHITE
CLOSING_COLOR: ManimColor = GOLD_D
COUNTER_COLOR: ManimColor = GRAY
DIM_COLOR: ManimColor = GRAY_D


# ---------------------------------------------------------------------------
# Typography helpers
# ---------------------------------------------------------------------------
def make_title_card(
    title: str,
    subtitle: str,
    title_font: int = 48,
    subtitle_font: int = 22,
) -> VGroup:
    """Full-screen title card — title + subtitle centred."""
    t: Text = Text(title, font_size=title_font, color=WHITE)
    s: Text = Text(subtitle, font_size=subtitle_font, color=GRAY)
    s.next_to(t, DOWN, buff=0.35)
    return VGroup(t, s)


def make_header(text: str, font_size: int = 34) -> Text:
    """Doubt header — large, coloured, top of screen."""
    return Text(text, font_size=font_size, color=HEADER_COLOR, weight=BOLD)


def make_bullet(text: str, font_size: int = 22, indent: float = 0.5) -> VGroup:
    """Single bullet point — dash + text, left-aligned."""
    dash: Text = Text("—", font_size=font_size, color=HEADER_COLOR)
    body: Text = Text(text, font_size=font_size, color=EXAMPLE_COLOR)
    body.next_to(dash, RIGHT, buff=0.2)
    group: VGroup = VGroup(dash, body)
    group.shift(RIGHT * indent)
    return group


def make_example_block(
    label: str,
    detail: str,
    label_font: int = 20,
    detail_font: int = 17,
    indent: float = 0.5,
) -> VGroup:
    """Two-line example: bold label + dimmer detail beneath."""
    lbl: Text = Text(label, font_size=label_font, color=GOLD_D, weight=BOLD)
    det: Text = Text(detail, font_size=detail_font, color=GRAY_B)
    det.next_to(lbl, DOWN, buff=0.08, aligned_edge=LEFT)
    group: VGroup = VGroup(lbl, det)
    group.shift(RIGHT * indent)
    return group


def make_closing(text: str, font_size: int = 20) -> Text:
    """Italicised closing observation — gold, bottom of screen."""
    return Text(
        f'"{text}"',
        font_size=font_size,
        color=CLOSING_COLOR,
        slant=ITALIC,
    )


def make_counter(current: int, total: int, font_size: int = 16) -> Text:
    """Top-right doubt counter — 'Doubt 2 of 6'."""
    return Text(
        f"Doubt {current} of {total}",
        font_size=font_size,
        color=COUNTER_COLOR,
    )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def stack_bullets(
    bullets: list[VGroup],
    start: np.ndarray,
    spacing: float = 0.55,
) -> VGroup:
    """Stack bullet VGroups vertically from *start* downward."""
    group: VGroup = VGroup(*bullets)
    group.arrange(DOWN, aligned_edge=LEFT, buff=spacing)
    group.move_to(start, aligned_edge=LEFT)
    return group


# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------
def animate_title_card(scene: Scene, card: VGroup, hold: float = 1.2) -> None:
    """Write title, fade subtitle, hold, then scale to corner."""
    title, subtitle = card[0], card[1]
    scene.play(Write(title), run_time=1.2)
    scene.play(FadeIn(subtitle, shift=UP * 0.1))
    scene.wait(hold)
    scene.play(card.animate.scale(0.38).to_corner(UL, buff=0.22))


def animate_header(
    scene: Scene,
    header: Text,
    position: np.ndarray | None = None,
) -> None:
    """Write header at position (default: top-centre)."""
    if position is not None:
        header.move_to(position)
    else:
        header.to_edge(UP, buff=0.5)
    scene.play(Write(header), run_time=0.9)


def animate_bullets_sequential(
    scene: Scene,
    bullets: list[VGroup],
    run_time: float = 0.5,
    wait: float = 0.4,
) -> None:
    """Fade in each bullet sequentially with a pause between."""
    for bullet in bullets:
        scene.play(FadeIn(bullet, shift=RIGHT * 0.15), run_time=run_time)
        scene.wait(wait)


def animate_closing(
    scene: Scene,
    closing: Text,
    hold: float = 1.8,
) -> None:
    """Fade in closing observation, hold, done."""
    closing.to_edge(DOWN, buff=0.5)
    scene.play(FadeIn(closing, shift=UP * 0.1))
    scene.wait(hold)


def animate_doubt_scene(
    scene: Scene,
    counter_text: str,
    header_text: str,
    examples: list[tuple[str, str]],
    closing_text: str,
    example_start: np.ndarray | None = None,
) -> None:
    """
    Full doubt scene template — composes all primitives in order:

    1. Counter (top-right)
    2. Header (top-centre)
    3. Examples fade in sequentially
    4. Closing observation
    5. Hold and fade out

    Parameters
    ----------
    counter_text : str
        e.g. "Doubt 1 of 6"
    header_text : str
        The doubt title.
    examples : list of (label, detail) tuples
        Each example rendered as a two-line block.
    closing_text : str
        The closing observation — will be quoted and italicised.
    example_start : np.ndarray, optional
        Where to begin stacking examples. Defaults to just below header.
    """
    # Counter
    counter: Text = Text(counter_text, font_size=16, color=COUNTER_COLOR)
    counter.to_corner(UR, buff=0.3)
    scene.play(FadeIn(counter), run_time=0.3)

    # Header
    header: Text = make_header(header_text)
    header.to_edge(UP, buff=0.55)
    scene.play(Write(header), run_time=0.9)
    scene.wait(0.3)

    # Examples
    if example_start is None:
        example_start = header.get_bottom() + DOWN * 0.6 + LEFT * 5.5

    example_mobs: list[VGroup] = [
        make_example_block(label, detail) for label, detail in examples
    ]
    stacked: VGroup = stack_bullets(example_mobs, start=example_start, spacing=0.65)

    for mob in example_mobs:
        scene.play(FadeIn(mob, shift=RIGHT * 0.15), run_time=0.5)
        scene.wait(0.45)

    scene.wait(0.3)

    # Closing
    closing: Text = make_closing(closing_text)
    closing.to_edge(DOWN, buff=0.45)
    scene.play(FadeIn(closing, shift=UP * 0.1))
    scene.wait(2.0)

    # Fade everything out
    scene.play(
        FadeOut(counter),
        FadeOut(header),
        FadeOut(stacked),
        FadeOut(closing),
        run_time=0.7,
    )
