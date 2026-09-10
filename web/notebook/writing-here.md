---
title: Writing here
sidebar_label: Writing here
sidebar_position: 5
description: Front matter, components, and conventions for pages on this site.
---

# Writing here

Everything on this page works in any `.md` or `.mdx` file under `blog/` or
`notebook/` with no imports. It doubles as the proof sheet: what you see below
is what the components look like.

## Where a piece goes

|  | Lives in | URL | Ordered by |
| --- | --- | --- | --- |
| Dated piece — a note, an essay, a session log | `blog/YYYY-MM-DD-slug.md` | `/writing/slug` | Date, newest first |
| Living page — revised in place | `notebook/project/page.md` | `/notebook/project/page` | Sidebar position |

The rule of thumb: if the date is part of what the piece means, it is writing.
If a reader six months from now should see the current version rather than the
original, it belongs in the notebook.

## Front matter

Dated pieces:

```yaml
---
title: "Watching a claim get smaller"
slug: watching-a-claim-get-smaller
authors: [saif]
tags: [lab-notes, knowledge-editing]
date: 2026-09-10
standfirst: >
  One sentence under the title saying what the piece argues.
status: provisional      # draft | provisional | standing | superseded
revised: 2026-09-24      # only if it differs from date
project: edit-slice
---
```

`standfirst`, `status`, `revised`, and `project` are optional; each one adds a
row to the front matter block at the top of the article. Everything after
`<!-- truncate -->` is hidden from the index.

Notebook pages take `title`, `sidebar_label`, `sidebar_position`, and
`description`. They show a "last edited" line taken from git, so revising a page
is recorded without you maintaining a date by hand.

## Figures

Numbering is a CSS counter, so figures renumber themselves when you move them.

```mdx
<Figure
  src="/img/edit-slice/orphan-diagram.svg"
  alt="An edited fact with its grounds left pointing at the old value"
  caption="Argument order swaps the edited triple. Justification order asks about the facts that were premises for it."
  wide
/>
```

<Figure
  plain
  caption="The two orders, side by side."
>
  <svg viewBox="0 0 560 150" role="img" aria-label="Argument order swaps the edited triple; justification order points at separate premise facts.">
    <g fill="none" stroke="#8798a5" strokeWidth="1">
      <rect x="8" y="20" width="250" height="110" rx="2" />
      <rect x="302" y="20" width="250" height="110" rx="2" />
    </g>
    <g fontFamily="IBM Plex Sans, sans-serif" fontSize="11" fill="#56697a">
      <text x="20" y="40">Argument order</text>
      <text x="314" y="40">Justification order</text>
    </g>
    <g fontFamily="IBM Plex Mono, monospace" fontSize="10.5" fill="#16283c">
      <text x="20" y="70">(Eiffel, in, Rome)</text>
      <text x="20" y="102">(Rome, contains, Eiffel)</text>
      <text x="314" y="70">(Eiffel, in, Rome)</text>
      <text x="314" y="102">(Eiffel, built-for, Expo 1889)</text>
    </g>
    <g stroke="#8c3a2e" strokeWidth="1">
      <path d="M112 78 L112 92" markerEnd="url(#arrow)" />
      <path d="M406 78 L406 92" markerEnd="url(#arrow)" />
    </g>
    <defs>
      <marker id="arrow" viewBox="0 0 8 8" refX="4" refY="4" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M1 1 L7 4 L1 7 z" fill="#8c3a2e" stroke="none" />
      </marker>
    </defs>
  </svg>
</Figure>

Put images in `static/img/<project>/`. A path of `/img/edit-slice/x.svg` resolves
correctly in development and on the deployed site.

## Claims

The claim block is the one loud element on the site. It shows what was given up
above what still stands, so a narrowing is visible rather than described.

```mdx
<Claim
  superseded="Everyone probes forward from an edit; nobody probes backward."
  record={{
    Confidence: "Medium",
    Revised: "10 September 2026",
  }}
>
  Argument-order inversion is covered. Justification order is not.
</Claim>
```

Use it once per page at most. Its force comes from being rare.

## Status marks

<Status kind="draft" /><br />
<Status kind="provisional" /><br />
<Status kind="standing" /><br />
<Status kind="superseded" />

```mdx
<Status kind="provisional" />
<Status kind="standing">Survived Arnab's review</Status>
```

For a whole page that is not finished, use the banner form:

<Notice>
  <strong>This page is scaffolding.</strong> The numbers in it are placeholders
  from a dry run and should not be cited.
</Notice>

## Margin notes

<Aside>
  On a wide screen this sits in the right margin, beside the paragraph it
  annotates. Below 1400px it folds into the column. Use it for the remark that
  would otherwise become a parenthesis three lines long.
</Aside>

Asides carry the qualification that would derail a sentence. They are not
footnotes — a footnote is for a citation or an aside a reader can skip entirely,
and this site has those too.[^1]

[^1]: Footnotes are plain Markdown: `[^1]` in the text, `[^1]: the note` at the
bottom of the file. They collect themselves into a block at the end.

## Mathematics

Inline math is written `$\mathrm{IIA}$`, which renders as $\mathrm{IIA}$.
Display math takes `$$`:

$$
\Delta_{\text{grounds}}(e) = \frac{1}{|G(e)|}
  \sum_{g \in G(e)} \mathbb{1}\!\left[\, \hat{y}(g) \neq y(g) \,\right]
$$

KaTeX renders at build time, so equations cost nothing at page load and are
selectable as text.

## Citing papers

Papers live once, in `data/papers.yml`, keyed by a citation id:

```yaml
cohen2024ripple:
  title: Evaluating the Ripple Effects of Knowledge Editing in Language Models
  authors: Cohen, R., Biran, E., Yoran, O., Globerson, A., Geva, M.
  year: 2024
  venue: TACL
  url: https://arxiv.org/abs/2307.12976
  status: read # read | skimmed | to-read
  relevance: high # to my current work
  verified: true # have I checked the venue against the paper?
  projects: [edit-slice]
  gives_me: The definition of Logical Generalization that narrowed my claim.
```

Cite it inline by id — <Cite id="cohen2024ripple" /> — and it links to the
paper with the full title on hover:

```mdx
The obvious place for it to break is RippleEdits <Cite id="cohen2024ripple" />.
As <Cite id="hase2023localization" narrative /> shows, localisation is not
editability.
```

`narrative` gives the "Hase et al. (2023)" form for when the authors are the
subject of the sentence rather than a parenthetical.

**The `verified` flag is the point of the whole thing.** An entry that came
from a literature map rather than the paper renders with a dotted oxide
underline — <Cite id="slaq" /> — and `/reading` lists those separately as not
citable yet. This exists because a note of mine described RippleEdits as EMNLP
2023 for months; it is TACL 2024. Secondhand notes decay silently, and an
unmarked wrong venue survives every draft.

An id with no entry shows up as <Cite id="nonexistent" /> rather than failing
the build, so a half-written draft still renders.

A reference list at the end of a piece pulls from the same file:

```mdx
<References ids={["cohen2024ripple", "meng2022rome", "meng2023memit"]} />
```

Use `items={[…]}` instead for a one-off that does not belong in the reading
list.

## Interactive pages

A standalone HTML page — plain HTML, CSS and JS, with its own interactions —
embeds as a live page rather than a screenshot. It shares numbering with
`<Figure>`, so a diagram and a demo are both "Figure n".

```mdx
<Embed
  src="https://your-page.netlify.app/"
  title="Belief revision explorer"
  caption="Contraction and expansion applied to the same belief set."
  ratio={16 / 10}
/>
```

Two ways to point at one:

**Hosted elsewhere.** Pass the full URL — a Netlify deploy, a GitHub Pages
site, anything served over HTTPS. Nothing to copy, and the page keeps updating
when you redeploy it. The one requirement is that the host does not send
`X-Frame-Options: DENY`; Netlify does not by default, so this works out of the
box.

**Served from this site.** Add the file to `data/built.yml`:

```yaml
- name: belief-revision
  title: The Belief Problem
  from: mind/belief-revision.html
  topic: Mind
  what: >
    What it takes to give up a belief, and why removing one is harder
    than adding one.
```

`npm run sync:demos` copies it to `static/demos/belief-revision/index.html`,
which happens automatically on `npm start` and `npm run build`. The entry also
becomes a card on [Built](/built) with a live preview. Then embed the path
anywhere you want it in prose:

```mdx
<Embed src="/demos/belief-revision/" title="Belief revision explorer" />
```

Paths in `data/built.yml` are relative to the repository root, and a directory
source is copied whole, so a page with sibling CSS, JS or data files works the
same way. Use `url:` instead of `from:` for a page deployed elsewhere and it
appears on Built the same way, marked with its host. Same-origin is the reason to prefer this route: the page can read
files next to it, and there is no third party to go down.

Either way the embed is sandboxed — scripts and forms run, top-level navigation
does not — and every embed carries a link to open the page on its own, because
an iframe on a phone is a poor place to use an interactive diagram.

Use a fixed `height` instead of `ratio` for a page that does not reflow:

```mdx
<Embed src="/demos/one-crate/" title="One crate" height={620} />
```

## The data files

Three files hold everything that appears on more than one page, so nothing is
described twice:

| File | Feeds |
| --- | --- |
| `data/papers.yml` | `<Cite>`, `<References ids>`, [Reading](/reading), the home page tally |
| `data/built.yml` | `npm run sync:demos`, [Built](/built), the home page list |
| blog front matter | [Writing](/writing), the home page list |

Adding a paper or a page means editing one file. The home page has no
hand-maintained lists.

## Syncing from a project

Notebook pages are ordinary files, so a project under
`~/code/open-concept-lab/ai/<project>/` can keep its own notes and have the page
here written from them. What works in practice is to keep the page shorter than
the notes: the notes are the record, the page is the argument. Copying notes
verbatim produces a page nobody reads, including you.

<References
  items={[
    {
      authors: "Cohen, R., Biran, E., Yoran, O., Globerson, A., Geva, M.",
      year: 2024,
      title:
        "Evaluating the Ripple Effects of Knowledge Editing in Language Models",
      venue: "TACL 12",
      url: "https://arxiv.org/abs/2307.12976",
    },
    {
      authors: "Meng, K., Bau, D., Andonian, A., Belinkov, Y.",
      year: 2022,
      title: "Locating and Editing Factual Associations in GPT",
      venue: "NeurIPS",
      url: "https://arxiv.org/abs/2202.05262",
    },
  ]}
/>
