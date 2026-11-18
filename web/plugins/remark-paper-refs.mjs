/**
 * Turn a paper's own cross-references into links, at build time.
 *
 * Two kinds of reference were being set as plain text and left to the reader:
 *
 *   §5.3          a section of this page
 *   [E-012]       a run in the provenance table at the foot of this page
 *
 * Neither could be clicked, so following one meant scrolling and counting
 * headings. This rewrites both into anchors while the page is being built, so
 * nothing in the Markdown changes and the PDF converter — which never sees this
 * plugin — keeps printing them as plain text, which is correct on paper.
 *
 * **Why the section map is built from the headings rather than written down.**
 * The slug of `### 5.3 Whose fact an edit changes…` is the whole sentence, and
 * these headings get rewritten. A hand-kept table of §5.3 → slug would go stale
 * silently, and on 18 November 2026 two hand-written anchors did exactly that
 * when three headings were reworded. Reading the headings in the same pass
 * cannot go stale: if the heading moves, the link moves with it.
 *
 * Headings are collected in full before any text is rewritten, because §5.6 is
 * routinely referred to from §1 — a single pass would miss every forward
 * reference.
 */
import GithubSlugger from "github-slugger";
import { visit, SKIP } from "unist-util-visit";

/** `5`, `5.3`, `5.3.1` at the head of a heading, with the rest ignored. */
const HEADING_NUMBER = /^\s*(\d+(?:\.\d+)*)[.)]?\s+\S/;

/** `§5`, `§5.3`, and `§§5.3` — but never a bare number. */
const SECTION_REF = /§§?\s?(\d+(?:\.\d+)*)/g;

/** `[E-012]`, `[F-07]`, and the non-breaking hyphen these ids are typeset with. */
const RUN_REF = /\[([EFRTD][-‐‑‒–]\d{2,3})\]/g;

const DASHES = /[-‐‑‒–]/g;

/** The ids are typeset with a non-breaking hyphen; links are not. */
function dehyphen(id) {
  return id.replace(DASHES, "-");
}

/** Flatten a heading's children to the text the slugger would have seen. */
function headingText(node) {
  let out = "";
  visit(node, (child) => {
    if (child.type === "text" || child.type === "inlineCode") out += child.value;
  });
  return out;
}

export default function remarkPaperRefs() {
  return (tree) => {
    /* Pass one: every heading, in document order, through one slugger — the
       same object Docusaurus uses, so a repeated heading gets the same `-1`
       suffix here as it does in the rendered anchor. */
    const slugger = new GithubSlugger();
    const sections = new Map();
    visit(tree, "heading", (node) => {
      const text = headingText(node);
      const slug = slugger.slug(text);
      const m = HEADING_NUMBER.exec(text);
      if (m && !sections.has(m[1])) {
        /* The slug to jump to, and the heading itself for the tip. The heading
           is a claim on this page, so hovering §5.6 shows what §5.6 found. */
        sections.set(m[1], { slug, title: text.replace(/^\s*\d+(?:\.\d+)*[.)]?\s+/, "").trim() });
      }
    });

    /* Which runs this page actually has a row for. A blog post can mention
       [E-016] with no provenance table anywhere on it, and linking that would
       send the reader to an anchor that does not exist — which the build's
       broken-anchor check catches, and which is how this was found. Only ids
       with a row on this page become links; the rest stay the plain text they
       already were. */
    const runs = new Map();
    visit(tree, ["mdxJsxFlowElement", "mdxJsxTextElement"], (node) => {
      if (node.name !== "Run") return;
      const attr = (node.attributes ?? []).find(
        (a) => a.type === "mdxJsxAttribute" && a.name === "id",
      );
      if (typeof attr?.value !== "string") return;
      /* The row's own one-line description, so a reference to it can say what
         it points at rather than only where it goes. It is the text already in
         the table; nothing is written twice. */
      /* First row wins, because two rows can share an id — one run swept two
         models and wrote a row for each — and a duplicate HTML id sends the
         browser to the first. Keeping the last description would describe a
         row the link does not land on. */
      const key = dehyphen(attr.value);
      if (!runs.has(key)) {
        runs.set(key, headingText(node).replace(/\s+/g, " ").trim());
      }
    });

    /* `Prov` is a component, so the plugin cannot rewrite what it renders — but
       it can hand it the description as a prop, which is the same data the
       plain-text references get. */
    visit(tree, ["mdxJsxFlowElement", "mdxJsxTextElement"], (node) => {
      if (node.name !== "Prov") return;
      const attrs = node.attributes ?? [];
      const idAttr = attrs.find((a) => a.type === "mdxJsxAttribute" && a.name === "id");
      if (typeof idAttr?.value !== "string") return;
      const detail = runs.get(dehyphen(idAttr.value));
      if (detail && !attrs.some((a) => a.name === "detail")) {
        attrs.push({ type: "mdxJsxAttribute", name: "detail", value: detail });
        node.attributes = attrs;
      }
    });

    if (!sections.size && !runs.size) return;

    /* Pass two: rewrite text nodes. Anything already inside a link is left
       alone — a reference inside a link would nest two anchors, which is
       invalid and which browsers resolve by dropping one of them. */
    visit(tree, "text", (node, index, parent) => {
      if (!parent || index === null) return;
      if (parent.type === "link" || parent.type === "linkReference") return;
      if (parent.type === "heading") return;

      const parts = [];
      let last = 0;
      const hits = [];
      for (const m of node.value.matchAll(SECTION_REF)) {
        const sec = sections.get(m[1]);
        if (sec) hits.push({ at: m.index, text: m[0], href: `#${sec.slug}`,
                             cls: "ocl-xref ocl-xref--section",
                             tip: `§${m[1]} — ${sec.title}` });
      }
      for (const m of node.value.matchAll(RUN_REF)) {
        const id = dehyphen(m[1]);
        if (!runs.has(id)) continue;
        hits.push({ at: m.index, text: m[0], href: `#run-${id}`,
                    cls: "ocl-xref ocl-xref--run",
                    tip: `${id} — ${runs.get(id)}` });
      }
      if (!hits.length) return;
      hits.sort((a, b) => a.at - b.at);

      for (const h of hits) {
        if (h.at < last) continue; // overlapping matches: keep the first
        if (h.at > last) parts.push({ type: "text", value: node.value.slice(last, h.at) });
        parts.push({
          type: "link",
          url: h.href,
          /* Not `title`: that is the browser's own tooltip, drawn in the system
             font on a system surface, and nothing can style it. The page draws
             its own from `data-tip`, and `aria-label` carries the same words to
             a screen reader, which a CSS tooltip alone never reaches. */
          data: {
            hProperties: {
              className: h.cls,
              ...(h.tip ? { "data-tip": h.tip, "aria-label": h.tip } : {}),
            },
          },
          children: [{ type: "text", value: h.text }],
        });
        last = h.at + h.text.length;
      }
      if (last < node.value.length) {
        parts.push({ type: "text", value: node.value.slice(last) });
      }
      parent.children.splice(index, 1, ...parts);
      return [SKIP, index + parts.length];
    });
  };
}
