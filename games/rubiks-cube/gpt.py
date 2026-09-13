import math
import random
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL

from OpenGL.GL import *
from OpenGL.GLU import *


# ============================================================
# Configuration
# ============================================================

CUBE_SIZE = 0.95
GAP = 0.055

COLORS = {
    "U": (1.0, 1.0, 1.0),      # White
    "D": (1.0, 0.85, 0.0),     # Yellow
    "F": (0.0, 0.65, 0.15),    # Green
    "B": (0.0, 0.30, 0.85),    # Blue
    "R": (0.85, 0.05, 0.05),    # Red
    "L": (1.0, 0.45, 0.05),     # Orange
}

BLACK = (0.035, 0.035, 0.035)


# ============================================================
# Cubie
# ============================================================

class Cubie:
    """
    A single cubie.

    position:
        integer coordinates in {-1, 0, 1}

    stickers:
        maps face -> color
        e.g. {"U": "U", "F": "F", "R": "R"}
    """

    def __init__(self, position):
        self.position = list(position)
        x, y, z = position

        self.stickers = {}

        if y == 1:
            self.stickers["U"] = "U"
        if y == -1:
            self.stickers["D"] = "D"
        if z == 1:
            self.stickers["F"] = "F"
        if z == -1:
            self.stickers["B"] = "B"
        if x == 1:
            self.stickers["R"] = "R"
        if x == -1:
            self.stickers["L"] = "L"


# ============================================================
# Rubik's Cube
# ============================================================

class RubiksCube:

    def __init__(self):
        self.cubies = []

        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                for z in (-1, 0, 1):
                    self.cubies.append(Cubie((x, y, z)))

        self.move_history = []

    # --------------------------------------------------------
    # Face selection
    # --------------------------------------------------------

    def get_layer(self, face):
        axis, value = {
            "U": ("y", 1),
            "D": ("y", -1),
            "R": ("x", 1),
            "L": ("x", -1),
            "F": ("z", 1),
            "B": ("z", -1),
        }[face]

        index = {"x": 0, "y": 1, "z": 2}[axis]

        return [
            cubie for cubie in self.cubies
            if cubie.position[index] == value
        ]

    # --------------------------------------------------------
    # Rotate a coordinate
    # --------------------------------------------------------

    @staticmethod
    def rotate_position(position, axis, clockwise):
        x, y, z = position

        if axis == "x":
            if clockwise:
                y, z = -z, y
            else:
                y, z = z, -y

        elif axis == "y":
            if clockwise:
                x, z = z, -x
            else:
                x, z = -z, x

        elif axis == "z":
            if clockwise:
                x, y = -y, x
            else:
                x, y = y, -x

        return [x, y, z]

    # --------------------------------------------------------
    # Rotate sticker directions
    # --------------------------------------------------------

    @staticmethod
    def rotate_sticker(face, axis, clockwise):

        vectors = {
            "U": (0, 1, 0),
            "D": (0, -1, 0),
            "F": (0, 0, 1),
            "B": (0, 0, -1),
            "R": (1, 0, 0),
            "L": (-1, 0, 0),
        }

        reverse = {
            v: k for k, v in vectors.items()
        }

        v = vectors[face]

        x, y, z = v

        if axis == "x":
            if clockwise:
                y, z = -z, y
            else:
                y, z = z, -y

        elif axis == "y":
            if clockwise:
                x, z = z, -x
            else:
                x, z = -z, x

        elif axis == "z":
            if clockwise:
                x, y = -y, x
            else:
                x, y = y, -x

        return reverse[(x, y, z)]

    # --------------------------------------------------------
    # Make a move
    # --------------------------------------------------------

    def move(self, notation):

        face = notation[0]

        clockwise = True

        if len(notation) > 1:
            if notation[1] == "'":
                clockwise = False

        axis = {
            "U": "y",
            "D": "y",
            "R": "x",
            "L": "x",
            "F": "z",
            "B": "z",
        }[face]

        # For opposite faces, invert direction so notation follows
        # standard Singmaster convention.
        if face in ("D", "L", "B"):
            clockwise = not clockwise

        turns = 2 if len(notation) > 1 and notation[1] == "2" else 1

        for _ in range(turns):

            layer = self.get_layer(face)

            for cubie in layer:

                cubie.position = self.rotate_position(
                    cubie.position,
                    axis,
                    clockwise
                )

                new_stickers = {}

                for sticker_face, color in cubie.stickers.items():

                    new_face = self.rotate_sticker(
                        sticker_face,
                        axis,
                        clockwise
                    )

                    new_stickers[new_face] = color

                cubie.stickers = new_stickers

        self.move_history.append(notation)

    # --------------------------------------------------------
    # Scramble
    # --------------------------------------------------------

    def scramble(self, length=20):

        faces = ["U", "D", "L", "R", "F", "B"]

        modifiers = ["", "'", "2"]

        last_face = None
        sequence = []

        for _ in range(length):

            face = random.choice(faces)

            while face == last_face:
                face = random.choice(faces)

            modifier = random.choice(modifiers)

            move = face + modifier

            self.move(move)

            sequence.append(move)

            last_face = face

        return sequence


# ============================================================
# OpenGL rendering
# ============================================================

def draw_cubelet(cubie):

    x, y, z = cubie.position

    spacing = CUBE_SIZE + GAP

    x *= spacing
    y *= spacing
    z *= spacing

    glPushMatrix()
    glTranslatef(x, y, z)

    draw_body()

    for face, color_name in cubie.stickers.items():
        draw_sticker(face, COLORS[color_name])

    glPopMatrix()


def draw_body():

    s = CUBE_SIZE / 2

    vertices = [
        (-s, -s, -s),
        ( s, -s, -s),
        ( s,  s, -s),
        (-s,  s, -s),

        (-s, -s,  s),
        ( s, -s,  s),
        ( s,  s,  s),
        (-s,  s,  s),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 4, 7, 3),
        (1, 5, 6, 2),
        (3, 2, 6, 7),
        (0, 1, 5, 4),
    ]

    glColor3f(*BLACK)

    glBegin(GL_QUADS)

    for face in faces:
        for index in face:
            glVertex3fv(vertices[index])

    glEnd()


def draw_sticker(face, color):

    s = CUBE_SIZE / 2
    inset = 0.09

    a = s - inset
    b = s - 0.015

    glColor3f(*color)

    glBegin(GL_QUADS)

    if face == "F":
        glVertex3f(-a, -a, b)
        glVertex3f(a, -a, b)
        glVertex3f(a, a, b)
        glVertex3f(-a, a, b)

    elif face == "B":
        glVertex3f(a, -a, -b)
        glVertex3f(-a, -a, -b)
        glVertex3f(-a, a, -b)
        glVertex3f(a, a, -b)

    elif face == "R":
        glVertex3f(b, -a, a)
        glVertex3f(b, -a, -a)
        glVertex3f(b, a, -a)
        glVertex3f(b, a, a)

    elif face == "L":
        glVertex3f(-b, -a, -a)
        glVertex3f(-b, -a, a)
        glVertex3f(-b, a, a)
        glVertex3f(-b, a, -a)

    elif face == "U":
        glVertex3f(-a, b, -a)
        glVertex3f(a, b, -a)
        glVertex3f(a, b, a)
        glVertex3f(-a, b, a)

    elif face == "D":
        glVertex3f(-a, -b, a)
        glVertex3f(a, -b, a)
        glVertex3f(a, -b, -a)
        glVertex3f(-a, -b, -a)

    glEnd()


# ============================================================
# Main application
# ============================================================

def main():

    pygame.init()

    width = 1000
    height = 750

    pygame.display.set_mode(
        (width, height),
        DOUBLEBUF | OPENGL
    )

    pygame.display.set_caption("Python Rubik's Cube")

    glEnable(GL_DEPTH_TEST)

    glClearColor(0.055, 0.055, 0.065, 1.0)

    glMatrixMode(GL_PROJECTION)

    gluPerspective(
        45,
        width / height,
        0.1,
        100.0
    )

    glMatrixMode(GL_MODELVIEW)

    cube = RubiksCube()

    # Camera rotation
    rot_x = -25
    rot_y = -35

    dragging = False
    last_mouse = None

    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 20)

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # --------------------------------------------
            # Mouse orbit
            # --------------------------------------------

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:
                    dragging = True
                    last_mouse = event.pos

                elif event.button == 4:
                    pass

                elif event.button == 5:
                    pass

            elif event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:

                if dragging:

                    x, y = event.pos

                    dx = x - last_mouse[0]
                    dy = y - last_mouse[1]

                    rot_y += dx * 0.6
                    rot_x += dy * 0.6

                    rot_x = max(-89, min(89, rot_x))

                    last_mouse = event.pos

            # --------------------------------------------
            # Keyboard
            # --------------------------------------------

            elif event.type == pygame.KEYDOWN:

                key = pygame.key.name(event.key).upper()

                if key == "ESC":
                    running = False

                elif key == "SPACE":

                    sequence = cube.scramble()

                    print(
                        "Scramble:",
                        " ".join(sequence)
                    )

                elif key == "R":
                    cube.move("R")

                elif key == "L":
                    cube.move("L")

                elif key == "U":
                    cube.move("U")

                elif key == "D":
                    cube.move("D")

                elif key == "F":
                    cube.move("F")

                elif key == "B":
                    cube.move("B")

                elif key == "Z":
                    # Undo last move
                    if cube.move_history:

                        last = cube.move_history.pop()

                        if len(last) == 1:
                            inverse = last + "'"

                        elif last[1] == "'":
                            inverse = last[0]

                        else:
                            inverse = last

                        cube.move_history.pop()
                        cube.move(inverse)
                        cube.move_history.pop()

                elif key == "RETURN":

                    cube = RubiksCube()

        # =================================================
        # Render
        # =================================================

        glClear(
            GL_COLOR_BUFFER_BIT |
            GL_DEPTH_BUFFER_BIT
        )

        glLoadIdentity()

        glTranslatef(0, 0, -8)

        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        for cubie in cube.cubies:
            draw_cubelet(cubie)

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()