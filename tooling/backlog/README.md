# backlog (`bl`)

A small project backlog that lives inside your repo. Epics, stories and tasks
in one readable JSON file, a command line to change them, and a board in the
browser to look at them or edit them. No accounts and no dependencies: plain
Python 3.8+ and one HTML file.

It grew out of Janaan's `tools/backlog.py` and was rebuilt here so it works
in any project.

## Install

Pick one.

```sh
# 1. As a command, in a venv
python3 -m venv .venv && source .venv/bin/activate
pip install -e ~/code/open-concept-lab/tooling/backlog

# 2. No install: link the shell shim onto your PATH
ln -s ~/code/open-concept-lab/tooling/backlog/bin/bl ~/.local/bin/bl
```

Check it: `bl --version`.

## 60-second tour

```sh
cd ~/code/my-project
bl init "My project"                       # creates .backlog/backlog.json
bl add epic "Ship v1"                      # -> EP-1
bl add story "Write the CLI" -p EP-1 -l cli -o saif     # -> ST-1
bl add task "Parse arguments" -p ST-1      # -> TK-1
bl set TK-1 -s doing -n "started on argparse"
bl tree                                    # the hierarchy, coloured, with progress
bl next                                    # what's in progress, what to pick up
bl board                                   # a read-only board in your browser
bl serve                                   # the same board, now editable
```

Commands work from any subfolder: `bl` walks up to the nearest
`.backlog/` the way git finds `.git/`. Use `bl -C path …` to point at another
project.

## Commands

| Command | What it does |
| --- | --- |
| `bl init [name] [--kinds epic:EP,story:ST,task:TK] [--statuses todo,doing,done]` | start a backlog here |
| `bl add KIND "title" [-p PARENT] [-s STATUS] [-o OWNER] [-n NOTE] [-r REF] [-l LABEL] [-b BLOCKER]` | add an item, prints its id |
| `bl set ID [-t TITLE] [-s STATUS] [-o OWNER] [-n NOTE] [-r REF] [-p NEW_PARENT] [--link ID] [-b ID] [-l LABEL]` | change an item; `--unlink`, `--unblock`, `--unlabel`, `--unref` undo; `-o ""` clears the owner |
| `bl show ID [--json]` | one item: chain, children, blockers, what it blocks, links, refs, notes |
| `bl tree [ID] [--open]` | the hierarchy with progress; `--open` hides done and dropped |
| `bl ls [text] [-s STATUS] [-o OWNER] [-l LABEL] [-e EPIC] [-k KIND] [-a]` | a flat filtered list (closed items need `-a` or `-s`) |
| `bl next [-n 5]` | in progress, in review, blocked, then the top to-dos |
| `bl board [--out FILE] [--no-open]` | writes `.backlog/board.html` and opens it; works offline, read-only |
| `bl serve [--port 8765] [--no-open]` | the editable board at `http://127.0.0.1:8765` |
| `bl import PATH` | bring in another `backlog.json` (this format or Janaan's) |

Repeatable flags (`-l`, `-r`, `-b`, `--link`) also take comma lists. Add
`--no-color` anywhere for plain output (or set `NO_COLOR`).

### Rules it keeps

- Each kind sits under the kind above it: a story needs an epic, a task needs
  a story. Moving with `-p` follows the same rule.
- Ids are never reused, even if you delete an item by hand.
- Notes are appended with the date and never rewritten.
- `--link` relates two items both ways. `--blocked-by` is one way; the other
  item shows it under "Blocks".
- A ref given as a path that exists is stored relative to the project root,
  so `bl set TK-1 -r ../docs/plan.md` from a subfolder does the right thing.

## The board

`bl board` (read-only) and `bl serve` (editable) show the same page:

- **Board, Tree, List** views. A strip of epics with progress rings sits on
  top; click one to filter to it.
- **Search and filters**: by text, epic, kind, owner, label, and "hide closed".
- **Detail panel** (click any item): its chain of parents, children with a
  progress ring, blocked by, blocks, linked, siblings, refs (open as links to
  files in the project), and dated notes. `#ST-4` in a note becomes a link.
- **Deep links**: `board.html#ST-4` or `http://127.0.0.1:8765/#ST-4` opens that item.
- **Keyboard**: `/` search, `j` `k` move, `Enter` open, `Esc` close, `b` `t` `l`
  switch views, `[` `]` collapse or expand the tree, `n` new item, `?` help.
- **Light and dark** follow your system; the half-moon button forces one.
- Works on a phone width (filters fold behind the filter button).

With `bl serve` you can also drag cards between status columns, rename, change
status and owner, add and remove labels, add notes, add children, link and
block items, and add refs. Every edit is written straight to
`.backlog/backlog.json`. The page checks the file every few seconds, so a
change you make with the CLI shows up on its own.

## The file

`.backlog/backlog.json`, meant to be committed:

```json
{
  "config": {
    "done": ["done"],
    "ignored": ["dropped"],
    "kinds": [
      {"name": "epic", "prefix": "EP"},
      {"name": "story", "prefix": "ST"},
      {"name": "task", "prefix": "TK"}
    ],
    "name": "My project",
    "statuses": ["todo", "doing", "blocked", "review", "done", "parked", "dropped"]
  },
  "next": {"EP": 2, "ST": 2, "TK": 2},
  "version": 1,
  "items": {
    "EP-1": {
      "blocked_by": [],
      "created": "2026-10-18",
      "id": "EP-1",
      "kind": "epic",
      "labels": [],
      "links": [],
      "notes": ["2026-10-18: everything needed for v1"],
      "owner": null,
      "parent": null,
      "refs": [],
      "status": "doing",
      "title": "Ship v1",
      "updated": "2026-10-18"
    }
  }
}
```

Keys are sorted, items appear in id order with a blank line between them, so
a diff shows exactly which item changed. You can edit `config` by hand: the
first status is where new items start, `done` counts toward progress,
`ignored` is left out of progress. `.backlog/board.html` is generated; add it
to `.gitignore` if you don't want it committed.

Every write takes a lock on `.backlog/.lock`, re-reads the file, applies one
change and replaces the file in one step. So a CLI edit and a browser edit
never overwrite each other; at worst the later one wins on the same field.

### Moving the Janaan backlog over

```sh
cd ~/code/janaan
bl init Janaan
bl import backlog/backlog.json      # ids kept (EP-1, ST-12, ...), counters carried over
```

Importing into a backlog that already has items gives the imported ones new
ids and rewrites their parents, links and blockers to match; each gets a
note saying what its old id was.

## Tests

```sh
cd ~/code/open-concept-lab/tooling/backlog
python3 -m unittest discover -s tests -v
```

23 tests: init, add, set, links and blockers, parent rules, finding the root
from a subfolder, ids never reused, the file staying stable, the static
board, import (both cases), and the server's API round trip including a CLI
edit between two browser edits.

## What's rough

- No delete. Use the `dropped` status (ids are never reused anyway).
- No undo in the browser. Git is the undo.
- Kinds are a strict ladder (epic > story > task). An item can't skip a level,
  and there's no free-form nesting.
- `bl serve` has no login; it only listens on 127.0.0.1 and refuses
  cross-origin writes. Don't expose it on a network.
- Drag and drop needs a mouse; on a phone, change status from the detail panel.
- Two people editing the same field at the same moment: the later save wins,
  silently.
- `#ID` linking in notes only recognises the configured prefixes.
- Editing `config` (kinds, statuses) is by hand in the JSON; there's no command
  for it yet.
