# Someday

Things I want to do, try, learn or make — written down so my head can stop
holding them. A file here is not a plan; it is a line I no longer have to
remember. They show up at /someday.

One idea per file, named like a journal entry: `YYYY-MM-DD-short-name.md`.

```md
---
title: A small box for the home that runs AI locally
kind: business        # business | try | learn | make
status: spark         # spark | exploring | tried | project | let-go
why: One line on why it pulls at me.   # optional
link: /notebook/some-project/          # optional, once it went somewhere
note: Why I let it go.                 # optional, for let-go
---

Anything longer goes here, in plain Markdown: paragraphs, - lists,
**bold**, *italic*, `code` and [links](https://example.com).
```

Quickest way in, from `web/`:

    npm run idea -- "the idea"
    npm run idea -- "the idea" --kind business --why "because…"

That writes the file with today's date and prints its path, so you can open it
and keep writing. Nothing gets deleted: a let-go idea stays, with its note.
