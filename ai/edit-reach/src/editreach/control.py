"""A reading that has no control does not exist.

edit-slice stated this as prose — *"Any script producing a ranking without both
controls is incomplete"* — and relied on whoever wrote the next script having
read it. Twice that nearly failed: [T-075] found layer 31 unreadable only
because the floor was carried alongside, and without it 0.699 would have looked
like a mild recovery from 0.633 rather than noise.

The lesson is sharper than "remember your controls". A coefficient of 1.000 is
almost **content-free on its own**, because a pipeline hard-wired to return 1
produces exactly the same number. What makes 1.000 mean something is that the
same code path returns 0.082 when a different subject's name is in the prompt.

So here the baseline is not an argument that may be omitted. `Reading` cannot be
constructed without one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence
import statistics

#: Different-subject coefficient at layer 5, Llama-3.1-8B [E-018]. A default to
#: compare against, never a substitute for measuring the floor in the same run.
REFERENCE_FLOOR_L5: Final[float] = 0.082


class Unbaselined(ValueError):
    """Raised when a reading is offered without the control that gives it meaning."""


@dataclass(frozen=True, slots=True)
class Baseline:
    """What the same pipeline returns when the signal should be absent.

    `values` are individual readings, not a pre-computed summary: the spread is
    what says whether the measure still discriminates at all. [T-075] found a
    layer where the floor had risen to meet the signal, and only the raw values
    showed it.
    """

    name: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise Unbaselined(f"baseline {self.name!r} carries no readings")

    @property
    def median(self) -> float:
        return statistics.median(self.values)

    @property
    def spread(self) -> float:
        return max(self.values) - min(self.values)

    @classmethod
    def of(cls, name: str, values: Sequence[float]) -> "Baseline":
        return cls(name=name, values=tuple(float(v) for v in values))


@dataclass(frozen=True, slots=True)
class Reading:
    """A measured quantity together with the control that makes it readable."""

    label: str
    value: float
    baseline: Baseline

    @property
    def margin(self) -> float:
        """How far the reading sits above its floor. The quantity worth reporting."""
        return self.value - self.baseline.median

    def discriminates(self, *, by: float = 0.10) -> bool:
        """Does the measure still tell signal from floor here?

        False does not mean the signal is absent. It means this measurement
        cannot say either way, which is a different finding and must not be
        reported as a null result. [T-075], layer 31.
        """
        return self.margin > by

    def __str__(self) -> str:
        verdict = "" if self.discriminates() else "  (floor has risen to meet it)"
        return (f"{self.label}: {self.value:.3f} against a {self.baseline.name} floor of "
                f"{self.baseline.median:.3f}, margin {self.margin:+.3f}{verdict}")


def require_baseline(value: float, baseline: Baseline | None, *, label: str) -> Reading:
    """Build a `Reading`, refusing when the control is missing.

    The refusal is the point. Call this instead of passing a bare float onward.
    """
    if baseline is None:
        raise Unbaselined(
            f"{label}: a coefficient without its floor is not a result. The same "
            f"pipeline must be run with a different subject, and that number carried "
            f"alongside this one."
        )
    return Reading(label=label, value=float(value), baseline=baseline)
