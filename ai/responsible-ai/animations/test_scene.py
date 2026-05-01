from manim import *


class HelloManim(Scene):
    def construct(self) -> None:
        text: Text = Text("Responsible AI", font_size=64)
        sub: Text = Text("NEU · INPR0340", font_size=28, color=GRAY)
        sub.next_to(text, DOWN, buff=0.4)

        self.play(Write(text))
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.wait(1.5)
