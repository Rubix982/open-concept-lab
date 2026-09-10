# Open Concept Lab — the site

Research writing, published as a working notebook. Docusaurus, restyled for
reading: prose in Spectral, apparatus (navigation, metadata, captions) in IBM
Plex Sans, mathematics via KaTeX.

```bash
npm install
npm start          # http://localhost:3000/open-concept-lab/
npm run build      # static output in build/
npm run typecheck
```

`npm start` and `npm run build` both run `sync:demos` first (see below).

## Where things go

| | Path | URL |
| --- | --- | --- |
| Dated pieces | `blog/YYYY-MM-DD-slug.md` | `/writing/slug` |
| Living project pages | `notebook/<project>/*.md` | `/notebook/<project>/…` |
| Papers | `data/papers.yml` | `/reading` |
| Project status | `data/projects.yml` + each `plan.md` | home page, `/notebook` |
| Standalone HTML pages | `data/built.yml` | `/built`, `/demos/<name>/` |
| Images | `static/img/<project>/` | `/img/<project>/…` |

Everything that appears on more than one page comes from a data source, so
there are no hand-maintained lists to fall out of date:

| Source | Feeds |
| --- | --- |
| `data/papers.yml` | `<Cite>`, `<References ids>`, `/reading`, home tally |
| `data/built.yml` | `npm run sync:demos`, `/built`, home list |
| `data/projects.yml` → each project's `plan.md` | `<Projects>`, home, `/notebook` |
| blog front matter | `/writing`, home list |

`projects.yml` holds only a path and a status colour; the objective and the
current phase are read out of each project's own `plan.md`. Editing a plan
updates the site.

Dependencies are managed with npm — `package-lock.json` is the only lockfile,
and CI runs `npm ci`.

The conventions page at `/notebook/writing-here` is the full reference — front
matter fields, every component, and what each one is for. Read that before
writing a new piece.

## Components

Available in any `.md` or `.mdx` file with no import:

- `<Figure>` — numbered figure, for an image or an inline diagram
- `<Embed>` — a live interactive HTML page, self-hosted or deployed elsewhere
- `<Cite id="…">` — inline citation resolved from `data/papers.yml`
- `<References ids={[…]}>` — numbered reference list from the same file
- `<Claim>` — a claim mid-revision: what was given up, above what stands
- `<Status>` / `<Notice>` — how settled a page or a claim is
- `<Aside>` — a margin note
- `<Projects>` — the project table, read from each `plan.md`

Registered in `src/theme/MDXComponents.tsx`; implementations in
`src/components/`.

## Interactive HTML pages

Two routes, both handled by `<Embed>`:

- **Hosted elsewhere** — give the entry a `url:`; nothing is copied
- **Served from here** — give it a `from:` path and `npm run sync:demos` copies
  it into `static/demos/<name>/`

Either way the page becomes a card on `/built` with a live preview, and can be
embedded in prose with `<Embed src="/demos/<name>/" title="…" />`. Paths are
relative to the repo root; a directory source is copied whole, so a page with
sibling CSS, JS or data files works. `static/demos` is generated and
gitignored.

## Citations

`data/papers.yml` is the single source. Each entry carries `status`,
`relevance`, `projects`, and a `verified` flag that records whether the venue
and year have been checked against the paper itself. Unverified entries render
with a dotted mark and are listed separately on `/reading`, so a secondhand
reference can't quietly pass for a checked one.

## Theme overrides

Kept deliberately small:

- `src/css/custom.css` — the whole design system, one file
- `src/theme/BlogPostItem/` — the front matter block and the index row
- `src/theme/BlogListPage/` — adds the lede above the index
- `plugins/lab-data.ts` — loads the data files and blog front matter, and
  exposes them to any page via `usePluginData("ocl-lab-data")`

Everything else is stock Docusaurus.
