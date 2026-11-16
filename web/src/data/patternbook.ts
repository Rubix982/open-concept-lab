// patternbook's runs, for /graphics/patternbook.
//
// patternbook is its own repository (github.com/Rubix982/patternbook), checked out here as the
// submodule projects/patternbook. `npm run sync:demos` copies its runs/ folder, the Lumenary
// engine that C-014's pages load, and the studio page for the engine's treatments, to
// /demos/patternbook/ (the `patternbook` entry in data/built.yml), so every page below opens
// as it was judged. The stills are made by
// scripts/patternbook-stills.sh.
//
// Everything in RUNS is copied from the repository's CARD.md at the commit in PINNED: the
// briefs, the verdicts, the word counts and the judge's words. Nothing updates itself.
//
// Adding a run, once it is committed and pushed in patternbook:
//   1. git submodule update --remote projects/patternbook   (from the repo root)
//   2. scripts/patternbook-stills.sh c015
//   3. add the card to RUNS below, from CARD.md, and move PINNED.

export const PATTERNBOOK = {
  repo: "https://github.com/Rubix982/patternbook",
  demos: "/demos/patternbook/runs",
  /** All of Lumenary's treatments with their dials; takes ?t=<id>, ?src=drawing, ?mode=sheet. */
  studio: "/demos/patternbook/treatments/lumenary.html",
  stills: "/img/graphics/patternbook",
};

export const PINNED = { commit: "fa12bf2", dates: "31 October and 16 November 2026", last: "C-014" };

// At PINNED, from README.md.
export const LIBRARY = { problemEntries: 2, artStyles: 3 };

/** "yes" and "no" answer a question asked of each page, not a pick between them. */
export type Verdict = "won" | "lost" | "tie" | "yes" | "no";

export type RunPage = {
  /** Path inside runs/, e.g. "c001/arm-b.html". */
  file: string;
  /** What the agent was given besides the brief. */
  given: string;
  /** Verdicts on the test's questions, in the order of `questions`. */
  verdicts?: Verdict[];
  words?: number;
  /** A file the agent was given, or wrote, as [label, path in the repository or a URL]. */
  source?: [string, string];
  /** Anything else the card recorded about this page, in one line. */
  notes?: string;
  /** What the close-up still shows; the still is then <card>-<page>-detail.webp. */
  detail?: string;
  /** What the judge later wrote about this page in C-010. */
  later?: string;
  /** The page's background and main accent. */
  swatch?: [string, string];
};

export type Run = {
  id: string;
  title: string;
  question: string;
  brief?: string;
  /** No agent built these pages; this file in the repository says how they were made. */
  made?: string;
  /** Short labels for the blind questions, then the questions in full. */
  questions?: [string, string][];
  pages: RunPage[];
  judge?: string[];
  /** C-005 only: each trait of the default, and on how many of the 7 pages it appeared. */
  traits?: [string, number][];
  /** C-005: many small windows in a row, instead of pairs. */
  layout?: "gallery";
  /** A line crediting work the test used: [text before, link label, URL, text after]. */
  credit?: [string, string, string, string];
  /** A link into the Lumenary studio: [label, query string]. */
  studio?: [string, string];
  showed: string;
};

const LUMENARY = "https://github.com/mursalfk/lumenary";

const ASSEMBLY = "library/step-by-step-instructions/ikea-assembly-instructions.md";

export const ASKED_AI = ["Less AI-made", "Which one would you point to as not looking AI-made?"] as [string, string];

export const RUNS: Run[] = [
  {
    id: "C-001",
    title: "A bike chain, with the IKEA entry and with nothing",
    question:
      "Does one entry, written from three IKEA bookcase manuals, change what an agent builds?",
    brief:
      "Build a single-page website that shows someone how to replace the chain on a bicycle. " +
      "Self-contained HTML/CSS, no external images — draw anything you need with SVG or CSS.",
    questions: [ASKED_AI],
    pages: [
      { file: "c001/arm-a.html", given: "No guidance", verdicts: ["lost"], words: 1140 },
      {
        file: "c001/arm-b.html",
        given: "The IKEA entry",
        verdicts: ["won"],
        words: 414,
        source: ["The entry, current version", ASSEMBLY],
      },
    ],
    judge: [
      "On the unguided page: “retro, 1980s… looks cool, but it's not a manual, more like a presentation.”",
      "On the entry page: “it has a genuine touch and a visual style”, though it needs more detail to feel like a proper manual.",
    ],
    showed:
      "The entry page applied all six of the entry's rules: a large step number and a line " +
      "drawing for each step, a parts grid whose labels come back inside the steps, magnified " +
      "callouts, crossed-out wrong ways, and black, white and grey only. The unguided page was " +
      "a text article. The entry agent also took about 13 minutes against 1.5, so the next test " +
      "checks whether any written reference would have done the same.",
  },
  {
    id: "C-002",
    title: "The IKEA entry against a reference the agent wrote for itself",
    question:
      "Did the C-001 page win because of what IKEA does, or because the agent had any reference to work from?",
    brief:
      "The same bike-chain brief. A third agent first wrote its own design reference in the " +
      "entry's five-part format, from its own judgement and no real source, then built from it.",
    questions: [
      ["Less AI-made", "Which one would you point to as not looking AI-made?"],
      ["Would use", "Which one would you rather have open while doing the job with greasy hands?"],
    ],
    pages: [
      {
        file: "c002/arm-c.html",
        given: "A reference it wrote for itself",
        verdicts: ["lost", "lost"],
        words: 1649,
        source: ["The reference it wrote", "runs/c002/self-reference.md"],
      },
      {
        file: "c001/arm-b.html",
        given: "The IKEA entry (the C-001 page)",
        verdicts: ["won", "won"],
        words: 414,
      },
    ],
    judge: ["On the self-reference page, before the reveal: “sooooooo text heavy.”"],
    showed:
      "The agent's own reference reached only 2 of the IKEA entry's 6 rules. The one it never " +
      "reached is letting the drawing carry the instruction, and its page had about four times " +
      "the words. Told to invent its own palette, it chose cream paper and orange, the same as " +
      "the unguided page.",
  },
  {
    id: "C-003",
    title: "The IKEA entry, checked against a chair, a chest of drawers and a lamp",
    question: "Were the entry's facts IKEA's habits, or a bookcase's?",
    pages: [],
    showed:
      "No pages built: this one read three more IKEA manuals. Only 6 of the entry's 14 facts " +
      "held in all three. Most of the rest turned out to be conditional: IKEA uses a device only " +
      "when the task has the problem it solves. Three of the six rules were narrowed.",
  },
  {
    id: "C-004",
    title: "A bike chain, with the revised IKEA entry and with the old one",
    question: "Did narrowing the rules after C-003 keep what made the entry win?",
    brief: "The same bike-chain brief, two new agents: one with the entry that won C-001, one with the revised entry.",
    questions: [
      ["Less AI-made", "Which one would you point to as not looking AI-made?"],
      ["Would use", "Which one would you rather have open while changing the chain with greasy hands?"],
    ],
    pages: [
      {
        file: "c004/arm-d.html",
        given: "The old entry",
        verdicts: ["lost", "won"],
        words: 261,
        source: ["The old entry", "runs/c004/entry-old.md"],
      },
      {
        file: "c004/arm-e.html",
        given: "The revised entry",
        verdicts: ["won", "lost"],
        words: 324,
        source: ["The revised entry", "runs/c004/entry-new.md"],
      },
    ],
    judge: ["On why the old entry's page was the one to use: “It was more concise, to me, but also laid it out step by step.”"],
    showed:
      "The two questions split. The revised page carried the reader's choice, quick link or " +
      "pin, across several steps as two branches. IKEA keeps a choice like that inside one step. " +
      "The rule now settles a choice in one place, and that change hasn't been tested.",
  },
  {
    id: "C-005",
    title: "Seven pages, nobody giving a style",
    question: "What does the agent build when it is given no style at all?",
    brief:
      "Five new agents, five briefs picked to pull the colours different ways: a neighbourhood " +
      "bakery, the docs homepage for a command-line tool, a wildlife photographer's portfolio, " +
      "a household energy dashboard, a lentil soup recipe. Plus the two bike-chain pages above " +
      "that were given no style.",
    layout: "gallery",
    pages: [
      { file: "c005/bakery.html", given: "Bakery", swatch: ["#f7f1e6", "#b4622d"] },
      { file: "c005/cli-docs.html", given: "Command-line tool docs", swatch: ["#f6f3ec", "#c2410c"] },
      { file: "c005/photographer.html", given: "Wildlife photographer", swatch: ["#f3efe6", "#a4552a"] },
      { file: "c005/energy.html", given: "Energy dashboard", swatch: ["#f5f4ef", "#2f6f4f"] },
      { file: "c005/recipe.html", given: "Lentil soup", swatch: ["#f7f1e6", "#c4552b"] },
      { file: "c001/arm-a.html", given: "Bike chain (C-001)", swatch: ["#f6f3ee", "#c4501f"] },
      { file: "c002/arm-c.html", given: "Bike chain, told to be original (C-002)", swatch: ["#f3efe6", "#c8471a"] },
    ],
    traits: [
      ["Warm off-white background, never white", 7],
      ["Warm near-black text, never pure black", 7],
      ["An orange or terracotta accent", 7],
      ["Uppercase, letter-spaced label above headings", 6],
      ["Pill-shaped chips", 5],
      ["Any older tell: Inter, a purple accent, a gradient", 1],
    ],
    showed:
      "The subject didn't move it. The command-line docs, a subject that suggests neutral or " +
      "dark, got cream paper and a #c2410c orange. The energy dashboard picked green first, on " +
      "the same cream, with orange for its peak readings. This became the checklist later tests " +
      "scored pages against.",
  },
  {
    id: "C-006",
    title: "Troubleshooting pages from four makers with no shared style",
    question: "Is there a convention for troubleshooting by symptom that holds across makers?",
    pages: [],
    showed:
      "No pages built: this one read the troubleshooting sections of a Miele dishwasher, a " +
      "Brother printer, a Toyota truck and a Garmin GPS. Six devices were constant across all " +
      "four: the symptom first, in the reader's terms; the cause stated apart from the fix; " +
      "several causes under one symptom; a named escalation last; long fixes linked out; short " +
      "imperatives. That became the second problem entry.",
  },
  {
    id: "C-007",
    title: "A router page, with the troubleshooting entry and with nothing",
    question: "Does the second entry beat the default on a product none of its four sources covers?",
    brief: "A troubleshooting page for a home Wi-Fi router.",
    questions: [
      ["Less AI-made", "Which one looks less AI-made?"],
      ["Would use", "Which one would you rather have open when your internet is down and you're trying to fix it?"],
    ],
    pages: [
      {
        file: "c007/arm-a.html",
        given: "No guidance",
        verdicts: ["tie", "won"],
        words: 399,
        later: "Visuals are very polygon-ish, no streaks, no flares, none of that human-touch",
      },
      {
        file: "c007/arm-b.html",
        given: "The troubleshooting entry",
        verdicts: ["tie", "lost"],
        words: 2466,
        later: "Too much text!",
        source: ["The entry, as tested", "runs/c007/entry.md"],
      },
    ],
    judge: [
      "“Page 2 has way more detail, but I like the attempt of visualization on page 1. Both look AI generated.”",
    ],
    showed:
      "The unguided page already followed five or six of the entry's six rules. What the entry " +
      "added was what printed manuals have because they are paper: a 19-symptom index, a table " +
      "of light states, error codes. That came to six times the words, and the page was harder " +
      "to use. Since then, an entry is written only after checking what the agent does unprompted.",
  },
  {
    id: "C-008",
    title: "A router page, with only IKEA's visual style and with nothing",
    question: "Can an art style, with no rules about structure, move a page off the AI look?",
    brief: "The C-007 router brief. One agent was given only an art-style file: IKEA's visual system, with no structural rules.",
    questions: [
      ["Less AI-made", "Which one looks less AI-made?"],
      ["Would use", "Which one would you rather have open when your internet is down?"],
    ],
    pages: [
      {
        file: "c008/arm-a.html",
        given: "No guidance",
        verdicts: ["lost", "lost"],
        words: 609,
        later: "The language is very… enthusiastic, very unnatural and uncanny like",
      },
      {
        file: "c008/arm-b.html",
        given: "IKEA's line-art style only",
        verdicts: ["won", "won"],
        words: 591,
        later:
          "the wide margins are so… neat and clean, it has an unremarkable cold finish that makes " +
          "it very unhuman, the top part is always so empty and fragile, and little, the header " +
          "section is almost non existent",
        source: ["The style file, as tested", "runs/c008/style.md"],
      },
    ],
    showed:
      "Same length and similar time, so effort doesn't explain it. With no structural rules, " +
      "the agent still organised the page as numbered picture panels; a style built around " +
      "numbered drawings seems to pull a page that way. Art style became its own part of the library. C-010 later " +
      "narrowed the win: this page drew the most criticism of the six, so it showed \"less " +
      "AI-made than the default\", not \"reads as human\".",
  },
  {
    id: "C-009",
    title: "Command-line docs, with a style from NASA's 1976 standards manual and with nothing",
    question: "Does a second, unrelated human style also move a page off the AI look?",
    brief: "C-005's brief: the docs homepage for an open-source command-line tool, the clearest case of the default ignoring the subject.",
    questions: [
      ["Less AI-made", "Which one looks less AI-made?"],
      ["Would use", "Which one would you rather use to learn and look up this tool?"],
    ],
    pages: [
      {
        file: "c009/arm-a.html",
        given: "No guidance",
        verdicts: ["tie", "won"],
        words: 650,
        later: "Very standard — fitting perhaps, as a very technical page",
      },
      {
        file: "c009/arm-b.html",
        given: "A typographic style from the NASA manual",
        verdicts: ["tie", "lost"],
        words: 627,
        later: "Empty spaces",
        source: ["The style file, as tested", "runs/c009/style.md"],
      },
    ],
    judge: ["“Both look AI-made.”"],
    showed:
      "The styled page followed its file closely and scored 0 of 5 on the default checklist, " +
      "against 5 of 5 for the unguided page, and the judge called both AI-made. So the checklist " +
      "doesn't predict the judgement, and the C-008 result doesn't yet extend to any human style.",
  },
  {
    id: "C-010",
    title: "What the judge actually sees as AI-made",
    question: "If not the palette, what is the judge reacting to?",
    pages: [],
    showed:
      "No new pages: the six router and docs pages from C-007 to C-009 were shown shuffled, and " +
      "the judge wrote what gives each away (the notes marked \"later\" above). Not one element " +
      "named was a palette trait. What was named: cold, empty white space, on both pages styled " +
      "from print; a missing header; enthusiastic copy; perfect vector drawings with no marks; " +
      "too much text. Those became the judge's checklist that C-011 was written against.",
  },
  {
    id: "C-011",
    title: "A router page, hand-inked in the style of the Army's PS Magazine, against line art",
    question: "Can a written style supply what the judge said was missing?",
    brief:
      "The C-007 router brief. The other page was given the line-art style from C-008, the " +
      "best result so far, so the bar was higher than the default.",
    questions: [
      ["Less AI-made", "Which one looks less AI-made?"],
      ["Would use", "Which one would you rather have open when your internet is down?"],
    ],
    pages: [
      {
        file: "c011/arm-a.html",
        given: "IKEA's line-art style",
        verdicts: ["lost", "lost"],
        words: 730,
        source: ["The style file, as tested", "runs/c011/style-lineart.md"],
      },
      {
        file: "c011/arm-b.html",
        given: "A hand-inked style from PS Magazine, 1953 and 1961",
        verdicts: ["won", "won"],
        words: 1450,
        source: ["The style file, as tested", "runs/c011/style-ps.md"],
      },
    ],
    judge: ["“Page 1! But it is bit harder to navigate the technical details, unlike page 2.”"],
    showed:
      "The PS Magazine page did what its file asked: a white page, near-black ink and one spot " +
      "blue, a schoolbook serif, hatching, and filters that roughen its lines so none is perfect. " +
      "It also has twice the words, so density and style aren't separated, and the judge's " +
      "notes on each page weren't collected this time.",
  },
  {
    id: "C-012",
    title: "The hand-inked router page, its drawings printed by a press treatment",
    question: "Does printing the drawings remove what the judge called “polygon-ish”?",
    brief:
      "No new agents. One page is the C-011 winner, unchanged. The other is the same page with " +
      "its ten drawn elements, the title lettering and nine drawings, run through press: a " +
      "two-colour letterpress model with ink spread, wobbling edges, misregistration, " +
      "dot-screened tints and grain, in the page's own two inks. Nothing else differs.",
    made: "runs/c012/prompts/README.md",
    questions: [
      ["Less AI-made", "Which page looks less AI-made?"],
      ["Drawings look printed", "On which page do the drawings look printed or hand-made rather than computer-drawn?"],
      ["Looks filtered", "Do the drawings on either page look “filtered”, like an effect laid on top?"],
    ],
    pages: [
      {
        file: "c012/arm-a.html",
        given: "The C-011 winner, untreated",
        verdicts: ["lost", "lost", "no"],
        detail: "Close-up: the drawings for steps 1 and 2, at twice the size",
      },
      {
        file: "c012/arm-b.html",
        given: "The same page, drawings printed with press",
        verdicts: ["won", "won", "yes"],
        detail: "The same close-up",
        source: ["The press treatment", "treatments/theory/press.md"],
      },
    ],
    showed:
      "The press page won both looks questions, and the judge called its drawings filtered. " +
      "Printing moved the drawings, and the page with them, away from computer-drawn, but it " +
      "shows as an effect, so the PS Magazine style names press only as a candidate. Why it " +
      "reads as filtered wasn't tested. From looking: every drawing got the same treatment in " +
      "equal measure, the drawings were already drawn to look hand-made before they were " +
      "printed, the small lettering inside them thickened, and the text beside them stayed crisp.",
  },
  {
    id: "C-013",
    title: "The same drawings printed two ways: press, and Lumenary's risograph model",
    question: "Did press's wobbling edges and ink spread cause the filtered look?",
    brief:
      "No new agents. One page is the C-012 press page. The other prints the same drawings with " +
      "riso: the same colour separation and inks, with Lumenary's risograph ink model at its " +
      "default dials. It keeps edges where they are, has no ink spread, lays tints as random " +
      "grain instead of a dot screen, and never prints ink fully solid.",
    made: "runs/c013/prompts/README.md",
    credit: [
      "The risograph ink model is from ",
      "Lumenary",
      LUMENARY,
      ", by Mursal Furqan Kumbhar, used with the author's permission.",
    ],
    studio: ["Try Lumenary's risograph model on the router drawing, with its dials", "?t=risograph&src=drawing"],
    questions: [
      ["Less AI-made", "Which page looks less AI-made?"],
      ["Drawings look printed", "On which page are the drawings more convincingly printed or hand-made?"],
      ["Looks more filtered", "Which page's drawings look more filtered, or neither, or both?"],
    ],
    pages: [
      {
        file: "c013/arm-a.html",
        given: "press, at C-012's dials (the C-012 page)",
        verdicts: ["tie", "tie", "no"],
        detail: "Close-up: the drawings for steps 1 and 2, at twice the size",
        source: ["The press treatment", "treatments/theory/press.md"],
      },
      {
        file: "c013/arm-b.html",
        given: "riso, Lumenary's risograph ink model",
        verdicts: ["tie", "tie", "yes"],
        detail: "The same close-up",
        source: ["The riso treatment", "treatments/theory/riso.md"],
      },
    ],
    judge: [
      "“Both are really good! One has darker lines, one has lighter lines.”",
      "On whether the drawings look printed: “Both are good!”",
    ],
    showed:
      "The riso page read as the more filtered of the two, and the other two questions tied. So C-012's " +
      "filtered look didn't come only from press's wobble and ink spread: a model with neither " +
      "read as more of an effect. Filtered turned out to be relative. The press page was the " +
      "filtered one beside the untreated page, and the less filtered one beside riso. The riso " +
      "page prints lines at about 80 to 95% black, which is the judge's “lighter lines”; whether that " +
      "is what reads as filtered is the next thing to test.",
  },
  {
    id: "C-014",
    title: "Three C-005 pages rebuilt with the Lumenary picture engine",
    question: "Do better pictures alone move a page off the AI look?",
    brief:
      "C-005's briefs for the bakery, the wildlife photographer and the lentil soup, word for " +
      "word, given to three new agents with one addition: make the page's pictures with the " +
      "Lumenary engine, from a short guide and a catalogue of its 214 treatments. No style file " +
      "and no problem entry. Each new page was picked blind against its C-005 counterpart.",
    credit: [
      "The engine is ",
      "Lumenary",
      LUMENARY,
      ", by Mursal Furqan Kumbhar, used with the author's permission.",
    ],
    studio: [
      "Try all 214 treatments in the Lumenary studio: one at a time with its dials, or every still treatment on one contact sheet",
      "",
    ],
    questions: [
      ["Less AI-made", "Which one looks less AI-made?"],
      ["Rather spend time on", "Which site would you rather spend time on?"],
    ],
    pages: [
      { file: "c005/bakery.html", given: "Bakery, no guidance (C-005)", verdicts: ["lost", "lost"], swatch: ["#f7f1e6", "#b4622d"] },
      {
        file: "c014/bakery.html",
        given: "Bakery, with the engine",
        verdicts: ["won", "won"],
        swatch: ["#f4ecdc", "#b2372a"],
        notes: "6 pictures: risograph, screen-print, rubber stamp. About 18 minutes.",
        source: ["The guide it was given", "runs/c014/lumenary-for-agents.md"],
      },
      { file: "c005/photographer.html", given: "Wildlife photographer, no guidance (C-005)", verdicts: ["tie", "lost"], swatch: ["#f3efe6", "#a4552a"] },
      {
        file: "c014/photographer.html",
        given: "Wildlife photographer, with the engine",
        verdicts: ["tie", "won"],
        swatch: ["#f1ede4", "#c8381c"],
        notes: "12 pictures: film grain, cyanotype. About 34 minutes.",
        source: ["The guide it was given", "runs/c014/lumenary-for-agents.md"],
      },
      { file: "c005/recipe.html", given: "Lentil soup, no guidance (C-005)", verdicts: ["won", "lost"], swatch: ["#f7f1e6", "#c4552b"] },
      {
        file: "c014/recipe.html",
        given: "Lentil soup, with the engine",
        verdicts: ["lost", "won"],
        swatch: ["#f3eee1", "#a3160f"],
        notes: "3 pictures: screen-print. About 16 minutes.",
        source: ["The guide it was given", "runs/c014/lumenary-for-agents.md"],
      },
    ],
    judge: [
      "On the photographer pair: “I love both! I think these are basic examples to show the " +
        "possible power of the engine, but we can explore more usages and see what people would like.”",
    ],
    showed:
      "The judge would rather spend time on the engine page in all three pairs, but it looked " +
      "less AI-made in only one, with one tie and one loss. The pictures changed and the page " +
      "around them didn't: all three engine pages kept a cream background, warm near-black " +
      "text, small uppercase labels and serif type, and the one warm accent moved from " +
      "terracotta to red. Out of 214 treatments, the agents used five. This fits C-010, where " +
      "four of the five things the judge named were about the page and one was about the " +
      "pictures. The judge could also tell the engine pages by their pictures, so these pairs " +
      "weren't blind in practice.",
  },
];

/** Tests that put two pages in front of the judge. */
export const BLIND = RUNS.filter((r) => r.questions);

/** Distinct pages the agents built, C-005's included; C-012's and C-013's are treated copies. */
export const BUILT = new Set(RUNS.filter((r) => !r.made).flatMap((r) => r.pages.map((p) => p.file))).size;

export const pageHref = (file: string): string => `${PATTERNBOOK.demos}/${file}`;
export const stillSrc = (page: RunPage): string =>
  `${PATTERNBOOK.stills}/${page.file.replace("/", "-").replace(/\.html$/, page.detail ? "-detail.webp" : ".webp")}`;
export const repoFile = (path: string): string =>
  /^https?:/.test(path) ? path : `${PATTERNBOOK.repo}/blob/${PINNED.commit}/${path}`;
export const promptFile = (file: string): string =>
  repoFile(`runs/${file.replace(/\/([^/]+)\.html$/, "/prompts/$1.md")}`);
