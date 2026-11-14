// Graphics: the computation that makes images, and the design of the pages they sit on.
//
// graphics-reuse lives in its own repository (github.com/Rubix982/graphics-reuse). The
// numbers in REUSE are copied from that repository's files, named beside each, as of
// AS_OF. They don't update themselves, so the date says how old they are. The test bed
// that supplied its one measurement is private and is not named anywhere on this site.
//
// patternbook's card is built from its entry in src/data/agentic.ts, so /agentic and
// /graphics can't disagree about it.

import { GUIDES } from "@site/src/data/agentic";

export const AS_OF = "14 November 2026";

export const REUSE = {
  repo: "https://github.com/Rubix982/graphics-reuse",
  entries: 4, // README.md, "Entries so far"
  measured: 1, // entries whose tested_in is filled
  readInFull: 1, // Brouet et al. 2012, agents/researcher/findings/r013/
  checks: 3, // R-004 and R-013 in CARD.md, R-011 in agents/researcher/tickets.md
};

export type GraphicsCard = {
  name: string; // the card's drawing is /img/art/tools/<name>.svg
  title: string;
  kind: string;
  plain: string; // what it is, in one sentence a newcomer can follow
  qa: [string, string][];
  use: string;
  useNote?: string;
  href: string;
  external: boolean;
};

const patternbook = GUIDES.find((g) => g.name === "patternbook");

export const GRAPHICS: GraphicsCard[] = [
  {
    name: "graphics-reuse",
    title: "graphics-reuse",
    kind: "Reference library",
    plain:
      "A reference of the ways graphics software avoids redoing work it has already done, " +
      "and of when the reused answer is still good enough.",
    qa: [
      [
        "What's in it",
        "One entry per technique: what work is wasted, how some field avoids it, when the " +
          "reuse stays valid, how it fails, and how to check it. Each condition says whether " +
          "it comes from a paper, a measurement, or reasoning nobody has tested.",
      ],
      [
        "Where it stands",
        "Four entries. One is measured in part and one is written from a full reading of its " +
          "paper. Three checks so far, each against what an AI agent already knows.",
      ],
    ],
    use: "git clone https://github.com/Rubix982/graphics-reuse\n# start with README.md, then CARD.md",
    useNote: "Literature first: reading papers and writing entries. No tooling yet.",
    href: "/graphics/reuse",
    external: false,
  },
  ...(patternbook
    ? [
        {
          name: patternbook.name,
          title: patternbook.title,
          kind: patternbook.kind,
          plain: patternbook.plain,
          qa: [
            ["What the agent does", patternbook.agent],
            ["What you get", patternbook.forYou],
          ] as [string, string][],
          use: patternbook.use,
          useNote: patternbook.useNote,
          href: patternbook.href,
          external: true,
        },
      ]
    : []),
];
