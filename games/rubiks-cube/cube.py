"""An interactive 3D Rubik's Cube.

Orbit the cube by dragging the background, turn a face by dragging a sticker,
scramble it, and wind the scramble back out.

Controls
    drag background      orbit the view
    drag a sticker       turn that face
    U D L R F B          turn a face (hold Shift for counter-clockwise)
    S                    scramble
    Enter                solve (replays the scramble backwards)
    scroll               zoom
    V                    reset the view
    Esc                  quit
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from typing import Final, Iterator

import numpy as np
import pygame
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_MODELVIEW,
    GL_MULTISAMPLE,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
    glVertex3f,
    glViewport,
)
from OpenGL.GLU import gluPerspective

Vec3 = tuple[float, float, float]
Color = tuple[float, float, float]

WINDOW_SIZE: Final[tuple[int, int]] = (900, 900)
FOV_DEGREES: Final[float] = 40.0
BACKGROUND: Final[Color] = (0.11, 0.12, 0.14)
PLASTIC: Final[Color] = (0.06, 0.06, 0.07)

# Standard Western colour scheme, keyed by the outward normal of the face.
FACE_COLORS: Final[dict[Vec3, Color]] = {
    (0.0, 1.0, 0.0): (0.97, 0.97, 0.97),    # up    - white
    (0.0, -1.0, 0.0): (0.98, 0.83, 0.08),   # down  - yellow
    (0.0, 0.0, 1.0): (0.00, 0.62, 0.28),    # front - green
    (0.0, 0.0, -1.0): (0.00, 0.32, 0.72),   # back  - blue
    (1.0, 0.0, 0.0): (0.79, 0.12, 0.14),    # right - red
    (-1.0, 0.0, 0.0): (0.95, 0.45, 0.08),   # left  - orange
}

# Corners of each face of a cube centred on the origin with half-extent 1,
# listed counter-clockwise as seen from outside.
FACE_CORNERS: Final[dict[Vec3, tuple[Vec3, Vec3, Vec3, Vec3]]] = {
    (0.0, 1.0, 0.0): ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)),
    (0.0, -1.0, 0.0): ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)),
    (0.0, 0.0, 1.0): ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)),
    (0.0, 0.0, -1.0): ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)),
    (1.0, 0.0, 0.0): ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)),
    (-1.0, 0.0, 0.0): ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)),
}

CUBIE_SIZE: Final[float] = 1.0
HALF: Final[float] = CUBIE_SIZE / 2.0
GAP: Final[float] = 0.06            # spacing between neighbouring cubies
STEP: Final[float] = CUBIE_SIZE + GAP
STICKER_SCALE: Final[float] = 0.86  # sticker inset within the cubie face
STICKER_LIFT: Final[float] = 0.006  # push stickers out to avoid z-fighting

DRAG_SENSITIVITY: Final[float] = 0.45  # degrees of orbit per pixel dragged
TURN_THRESHOLD: Final[float] = 14.0    # pixels of drag before a turn commits
MIN_ZOOM: Final[float] = 6.5
MAX_ZOOM: Final[float] = 24.0
DEFAULT_ZOOM: Final[float] = 11.0

TURN_SECONDS: Final[float] = 0.16
SCRAMBLE_SECONDS: Final[float] = 0.08
SCRAMBLE_LENGTH: Final[int] = 25

# Keyboard face turns: key -> (axis index, layer, direction of a clockwise turn
# seen from outside that face).
KEY_MOVES: Final[dict[int, tuple[int, int, int]]] = {
    pygame.K_u: (1, 1, -1),
    pygame.K_d: (1, -1, 1),
    pygame.K_r: (0, 1, -1),
    pygame.K_l: (0, -1, 1),
    pygame.K_f: (2, 1, -1),
    pygame.K_b: (2, -1, 1),
}

AXES: Final[tuple[Vec3, Vec3, Vec3]] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)


def rotation_matrix(axis: Vec3, degrees: float) -> np.ndarray:
    """A 4x4 right-handed rotation about `axis` (assumed unit length)."""
    theta = np.radians(degrees)
    x, y, z = axis
    c, s, t = np.cos(theta), np.sin(theta), 1.0 - np.cos(theta)
    m = np.identity(4, dtype=np.float32)
    m[:3, :3] = [
        [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
    ]
    return m


def gl_mult(m: np.ndarray) -> None:
    """Feed a row-major 4x4 to OpenGL, which wants column-major."""
    glMultMatrixf(np.ascontiguousarray(m.T, dtype=np.float32))


@dataclass
class Move:
    """A quarter turn of one layer.

    `axis` is 0/1/2 for x/y/z, `layer` is the coordinate of the layer along
    that axis, and `direction` is +1 or -1 for a right-handed turn about the
    positive axis. `record` is False for moves that undo history.
    """

    axis: int
    layer: int
    direction: int
    record: bool = True

    @property
    def inverse(self) -> "Move":
        return Move(self.axis, self.layer, -self.direction, record=False)

    def matrix(self, degrees: float) -> np.ndarray:
        return rotation_matrix(AXES[self.axis], degrees * self.direction)


@dataclass
class Cubie:
    """One of the 26 visible small cubes.

    `position` is where it currently sits on the -1..1 grid, `home` is where
    it belongs. `orientation` tracks how far it has been twisted; the sticker
    colours are fixed in the cubie's own frame and never change.
    """

    home: np.ndarray
    position: np.ndarray
    orientation: np.ndarray = field(
        default_factory=lambda: np.identity(3, dtype=np.float32)
    )
    stickers: dict[Vec3, Color] = field(default_factory=dict)

    def apply(self, rotation: np.ndarray) -> None:
        r = rotation[:3, :3]
        self.position = np.rint(r @ self.position).astype(np.int8)
        self.orientation = r @ self.orientation


class Cube:
    """Cube state plus the queue of turns waiting to be animated."""

    def __init__(self) -> None:
        self.cubies: list[Cubie] = []
        for x, y, z in _grid():
            home = np.array((x, y, z), dtype=np.int8)
            stickers = {
                normal: FACE_COLORS[normal]
                for normal in FACE_CORNERS
                if int(np.dot(normal, home)) == 1
            }
            self.cubies.append(
                Cubie(home=home, position=home.copy(), stickers=stickers)
            )

        self.queue: list[Move] = []
        self.history: list[Move] = []
        self.active: Move | None = None
        self.progress: float = 0.0
        self.speed: float = TURN_SECONDS

    @property
    def busy(self) -> bool:
        return self.active is not None or bool(self.queue)

    @property
    def solved(self) -> bool:
        return all(
            np.array_equal(c.position, c.home)
            and np.allclose(c.orientation, np.identity(3), atol=1e-3)
            for c in self.cubies
        )

    def enqueue(self, *moves: Move, speed: float = TURN_SECONDS) -> None:
        self.queue.extend(moves)
        self.speed = speed

    def scramble(self) -> None:
        moves: list[Move] = []
        last_axis = -1
        for _ in range(SCRAMBLE_LENGTH):
            axis = random.choice([a for a in range(3) if a != last_axis])
            last_axis = axis
            moves.append(
                Move(axis, random.choice((-1, 1)), random.choice((-1, 1)))
            )
        self.enqueue(*moves, speed=SCRAMBLE_SECONDS)

    def solve(self) -> None:
        """Wind the recorded history back out, most recent move first."""
        undo = [m.inverse for m in reversed(self.history)]
        self.history.clear()
        self.enqueue(*undo, speed=SCRAMBLE_SECONDS)

    def layer_of(self, move: Move) -> list[Cubie]:
        return [c for c in self.cubies if c.position[move.axis] == move.layer]

    def update(self, dt: float) -> None:
        if self.active is None:
            if not self.queue:
                return
            self.active, self.progress = self.queue.pop(0), 0.0

        self.progress += dt / self.speed
        if self.progress < 1.0:
            return

        move = self.active
        for cubie in self.layer_of(move):
            cubie.apply(move.matrix(90.0))
        if move.record:
            self.history.append(move)
        self.active, self.progress = None, 0.0

    def animation_matrix(self, cubie: Cubie) -> np.ndarray | None:
        """The partial rotation to apply while a turn is in flight."""
        move = self.active
        if move is None or cubie.position[move.axis] != move.layer:
            return None
        eased = self.progress * self.progress * (3.0 - 2.0 * self.progress)
        return move.matrix(90.0 * eased)


def _grid() -> Iterator[tuple[int, int, int]]:
    """Grid coordinates of the 26 visible cubies; the core is never seen."""
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                if (x, y, z) != (0, 0, 0):
                    yield x, y, z


def draw_cubie(cubie: Cubie, animation: np.ndarray | None) -> None:
    """Draw one small cube: black body plus its stickers."""
    model = np.identity(4, dtype=np.float32)
    model[:3, 3] = cubie.position * STEP
    model[:3, :3] = cubie.orientation
    if animation is not None:
        model = animation @ model

    glPushMatrix()
    gl_mult(model)

    glColor3f(*PLASTIC)
    glBegin(GL_QUADS)
    for corners in FACE_CORNERS.values():
        for cx, cy, cz in corners:
            glVertex3f(cx * HALF, cy * HALF, cz * HALF)
    glEnd()

    for normal, color in cubie.stickers.items():
        n = np.array(normal, dtype=np.float32)
        glColor3f(*color)
        glBegin(GL_QUADS)
        for corner in FACE_CORNERS[normal]:
            v = np.array(corner, dtype=np.float32) * HALF
            # Shrink only within the face plane; the normal component is
            # already pinned to the surface and would sink if scaled too.
            along = np.dot(v, n) * n
            glVertex3f(*((v - along) * STICKER_SCALE + along + n * STICKER_LIFT))
        glEnd()

    glPopMatrix()


@dataclass
class Hit:
    """Where a ray from the cursor met the cube."""

    cubie: Cubie
    normal: np.ndarray  # outward face normal, in cube space


def cast_ray(cube: Cube, mouse: tuple[int, int], size: tuple[int, int],
             view: np.ndarray, distance: float) -> Hit | None:
    """Find the sticker under the cursor, if any."""
    width, height = size
    tan_fov = np.tan(np.radians(FOV_DEGREES) / 2.0)
    ndc_x = (2.0 * mouse[0] / width - 1.0) * (width / height) * tan_fov
    ndc_y = (1.0 - 2.0 * mouse[1] / height) * tan_fov

    # The model matrix is translate(0,0,-distance) @ view, so invert both to
    # carry the eye-space ray back into the cube's own frame.
    rot = view[:3, :3]
    origin = rot.T @ np.array([0.0, 0.0, distance], dtype=np.float32)
    direction = rot.T @ np.array([ndc_x, ndc_y, -1.0], dtype=np.float32)

    best: Hit | None = None
    best_t = np.inf
    for cubie in cube.cubies:
        center = cubie.position.astype(np.float32) * STEP
        t, normal = _intersect_box(origin, direction, center, HALF)
        if t is not None and t < best_t:
            best_t, best = t, Hit(cubie, normal)
    return best


def _intersect_box(origin: np.ndarray, direction: np.ndarray,
                   center: np.ndarray, half: float
                   ) -> tuple[float | None, np.ndarray]:
    """Slab test against an axis-aligned box; returns entry t and its normal."""
    t_near, t_far = -np.inf, np.inf
    normal = np.zeros(3, dtype=np.float32)
    for axis in range(3):
        d = direction[axis]
        lo, hi = center[axis] - half, center[axis] + half
        if abs(d) < 1e-8:
            if not lo <= origin[axis] <= hi:
                return None, normal
            continue
        t1, t2 = (lo - origin[axis]) / d, (hi - origin[axis]) / d
        sign = -1.0 if t1 < t2 else 1.0
        t1, t2 = min(t1, t2), max(t1, t2)
        if t1 > t_near:
            t_near = t1
            normal = np.zeros(3, dtype=np.float32)
            normal[axis] = sign
        t_far = min(t_far, t2)
        if t_near > t_far:
            return None, normal
    return (t_near, normal) if t_far >= max(t_near, 0.0) else (None, normal)


def move_from_drag(hit: Hit, drag: tuple[float, float],
                   view: np.ndarray) -> Move | None:
    """Turn a screen-space drag on a sticker into the layer turn it implies."""
    # Screen coordinates with y pointing up, to match OpenGL's convention.
    wanted = np.array([drag[0], -drag[1]], dtype=np.float32)

    best_axis: np.ndarray | None = None
    best_score = 0.0
    for axis in AXES:
        candidate = np.array(axis, dtype=np.float32)
        if abs(np.dot(candidate, hit.normal)) > 0.5:
            continue  # not in the face plane
        on_screen = (view[:3, :3] @ candidate)[:2]
        score = float(np.dot(on_screen, wanted))
        if abs(score) > abs(best_score):
            best_score, best_axis = score, candidate

    if best_axis is None or best_score == 0.0:
        return None

    # Rotating about `motion x normal` sends the grabbed sticker along
    # `motion`: (m x n) x n == m for m perpendicular to n.
    motion = best_axis * np.sign(best_score)
    spin = np.cross(motion, hit.normal)
    index = int(np.argmax(np.abs(spin)))
    return Move(index, int(hit.cubie.position[index]), int(np.sign(spin[index])))


def setup_projection(width: int, height: int) -> None:
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV_DEGREES, width / max(height, 1), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)


def initial_view() -> np.ndarray:
    """A three-quarter view, so three faces are visible at startup."""
    return rotation_matrix((1.0, 0.0, 0.0), 22.0) @ rotation_matrix(
        (0.0, 1.0, 0.0), -35.0
    )


def caption(cube: Cube) -> str:
    if cube.busy:
        return "Rubik's Cube - turning..."
    if cube.solved:
        return "Rubik's Cube - solved  |  drag a sticker, S scramble, Enter solve"
    return "Rubik's Cube - drag a sticker to turn  |  S scramble, Enter solve"


def main() -> int:
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
    pygame.display.set_mode(
        WINDOW_SIZE, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
    )

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_MULTISAMPLE)
    glClearColor(*BACKGROUND, 1.0)
    setup_projection(*WINDOW_SIZE)

    cube = Cube()
    view = initial_view()
    distance = DEFAULT_ZOOM
    size = WINDOW_SIZE
    orbiting = False
    grab: Hit | None = None
    drag = np.zeros(2, dtype=np.float32)
    clock = pygame.time.Clock()
    shown = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return 0

            elif event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                setup_projection(*size)

            elif event.type == pygame.KEYDOWN:
                shift = bool(event.mod & pygame.KMOD_SHIFT)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return 0
                if event.key == pygame.K_s and not shift:
                    cube.scramble()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    cube.solve()
                elif event.key == pygame.K_v:
                    view, distance = initial_view(), DEFAULT_ZOOM
                elif event.key in KEY_MOVES:
                    axis, layer, direction = KEY_MOVES[event.key]
                    cube.enqueue(
                        Move(axis, layer, -direction if shift else direction)
                    )

            elif event.type == pygame.MOUSEWHEEL:
                distance = float(
                    np.clip(distance - event.y * 0.6, MIN_ZOOM, MAX_ZOOM)
                )

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                drag[:] = 0.0
                hit = None if cube.busy else cast_ray(
                    cube, event.pos, size, view, distance
                )
                if hit is None:
                    orbiting = True
                else:
                    grab = hit

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                orbiting, grab = False, None

            elif event.type == pygame.MOUSEMOTION:
                dx, dy = event.rel
                if orbiting:
                    # Left-multiply so the drag turns the cube about the
                    # screen's axes, not the cube's own rotated ones.
                    view = (
                        rotation_matrix((1.0, 0.0, 0.0), dy * DRAG_SENSITIVITY)
                        @ rotation_matrix((0.0, 1.0, 0.0), dx * DRAG_SENSITIVITY)
                        @ view
                    )
                elif grab is not None:
                    drag += (dx, dy)
                    if float(np.hypot(*drag)) >= TURN_THRESHOLD:
                        move = move_from_drag(grab, (drag[0], drag[1]), view)
                        if move is not None:
                            cube.enqueue(move)
                        grab = None

        cube.update(clock.get_time() / 1000.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        camera = np.identity(4, dtype=np.float32)
        camera[2, 3] = -distance
        gl_mult(camera)
        gl_mult(view)

        for cubie in cube.cubies:
            draw_cubie(cubie, cube.animation_matrix(cubie))

        pygame.display.flip()

        title = caption(cube)
        if title != shown:
            pygame.display.set_caption(title)
            shown = title

        clock.tick(60)


if __name__ == "__main__":
    sys.exit(main())
