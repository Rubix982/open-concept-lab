import type { ReactNode } from "react";

/**
 * No left rail on notebook pages.
 *
 * Two passes tried to make one legible and both failed in the same way: a rail
 * carrying five names, five stages, five descriptions and the pages under them
 * is a second index competing with the first, and the reader has to parse it on
 * every page to find the one row that is not noise.
 *
 * Looked at what this field's own sites do, on 10 November 2026.
 * transformer-circuits.pub — the closest reference there is — has no left rail
 * at all: one column, grouped by month, each entry carrying an author line and
 * a sentence. Anthropic's research index has none either; it opens with topic
 * tiles and counts, then cards with a label, a date and a summary. Both put the
 * navigating in an index page and give the article the width.
 *
 * So the rail is gone and the Notebook index does that work. `sidebars.ts`
 * stays: it still orders the pages, and the index renders the same tree the
 * rail used to, so there is one source for what a project's pages are.
 *
 * The cost is real and worth naming: moving between two projects now goes
 * through the index. For five projects that is one click; if this grows to
 * twenty it stops being acceptable and the rail should come back as plain
 * names.
 */
export default function DocRootLayoutSidebar(): ReactNode {
  return null;
}
