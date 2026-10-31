"""Moved to `editreach.local`. This file is a shim.

The measurement code now lives in `ai/edit-reach` as an installable package, so
there is one copy of it rather than two. Seventy-nine scripts in this repo import
`probing` by its old flat name and their results are already recorded in
`results/`; rewriting them would risk moving numbers for no gain, so the old
name keeps working and forwards here.

**New code should import `editreach.local` directly.** Nothing should be added
to this file.
"""

from __future__ import annotations

from editreach.local import *          # noqa: F401,F403
