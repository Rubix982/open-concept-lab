import fs from "node:fs/promises";
import path from "node:path";
import { load as parseYaml } from "js-yaml";
import {
  DEFAULT_PARSE_FRONT_MATTER,
  createExcerpt,
  parseMarkdownFile,
} from "@docusaurus/utils";
import type { LoadContext, Plugin } from "@docusaurus/types";

export type PaperStatus = "read" | "skimmed" | "to-read";
export type Relevance = "high" | "medium" | "low";

export type Paper = {
  id: string;
  title: string;
  authors: string;
  year: number;
  venue?: string;
  url?: string;
  status: PaperStatus;
  relevance: Relevance;
  /** False when the entry came from a secondhand note and is not citable yet. */
  verified: boolean;
  projects: string[];
  gives_me?: string;
};

export type BuiltPage = {
  name: string;
  title: string;
  topic: string;
  what: string;
  /** Site-relative path for a copied page, or an absolute URL. */
  src: string;
  external: boolean;
  /** Where the source lives, for the card's provenance line. */
  origin: string;
  ratio: number;
};

export type Project = {
  name: string;
  /** Short phase label — "Phase 1 — Design". */
  phase: string;
  /** The whole Current Phase paragraph, for the title attribute. */
  phaseDetail: string;
  /** The Objective paragraph, markdown stripped. */
  what: string;
  /** ISO date from the plan's "_Last updated:_" line, when present. */
  updated?: string;
  notebook: string;
  tone: string;
};

export type WritingEntry = {
  title: string;
  slug: string;
  permalink: string;
  date: string;
  summary: string;
  status?: string;
  project?: string;
  tags: string[];
};

export type LabData = {
  writing: WritingEntry[];
  papers: Paper[];
  built: BuiltPage[];
  projects: Project[];
};

const DATED_FILE = /^(\d{4})-(\d{2})-(\d{2})-(.+)\.mdx?$/;

async function readYaml<T>(file: string): Promise<T | undefined> {
  try {
    return parseYaml(await fs.readFile(file, "utf8")) as T;
  } catch {
    return undefined;
  }
}

async function loadWriting(
  blogDir: string,
  routeBasePath: string,
): Promise<WritingEntry[]> {
  let files: string[] = [];
  try {
    files = await fs.readdir(blogDir);
  } catch {
    return [];
  }

  const entries = await Promise.all(
    files
      .map((file) => ({ file, match: DATED_FILE.exec(file) }))
      .filter(
        (c): c is { file: string; match: RegExpExecArray } => c.match !== null,
      )
      .map(async ({ file, match }) => {
        const [, year, month, day, name] = match;
        const fileContent = await fs.readFile(path.join(blogDir, file), "utf8");
        const { frontMatter, content } = await parseMarkdownFile({
          filePath: file,
          fileContent,
          parseFrontMatter: DEFAULT_PARSE_FRONT_MATTER,
        });
        const fm = frontMatter as Record<string, unknown>;
        const slug =
          typeof fm.slug === "string" && fm.slug.length > 0 ? fm.slug : name;

        return {
          title: typeof fm.title === "string" ? fm.title : slug,
          slug,
          permalink: `/${routeBasePath}/${slug.replace(/^\//, "")}`,
          date:
            typeof fm.date === "string" ? fm.date : `${year}-${month}-${day}`,
          summary:
            (typeof fm.standfirst === "string" && fm.standfirst) ||
            (typeof fm.description === "string" && fm.description) ||
            createExcerpt(content) ||
            "",
          status: typeof fm.status === "string" ? fm.status : undefined,
          project: typeof fm.project === "string" ? fm.project : undefined,
          tags: Array.isArray(fm.tags)
            ? fm.tags.filter((t): t is string => typeof t === "string")
            : [],
        } satisfies WritingEntry;
      }),
  );

  entries.sort((a, b) => (a.date < b.date ? 1 : -1));
  return entries;
}

/** Markdown emphasis and code spans read as noise in a table cell. */
function stripMarkdown(text: string): string {
  return text
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\*\*([^*]*)\*\*/g, "$1")
    .replace(/\*([^*]*)\*/g, "$1")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

/** The first paragraph under a `## Heading`, as one line. */
function sectionParagraph(markdown: string, heading: string): string {
  const section = markdown.split(new RegExp(`^## ${heading}\\s*$`, "m"))[1];
  if (!section) {
    return "";
  }
  const body = section.split(/^## /m)[0] ?? "";
  const paragraph = body.trim().split(/\n\s*\n/)[0] ?? "";
  return stripMarkdown(paragraph);
}

const ABBREVIATIONS = ["e.g", "i.e", "cf", "vs", "et al", "Fig", "eq"];

/**
 * Trims to whole sentences rather than mid-clause. Splits only on a period
 * outside parentheses that does not end a known abbreviation, then keeps
 * sentences while under the soft limit — always at least one, so a single
 * long sentence survives intact rather than being cut.
 */
function summarize(text: string, softLimit: number): string {
  if (text.length <= softLimit) {
    return text;
  }

  const sentences: string[] = [];
  let depth = 0;
  let start = 0;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === "(" || ch === "[") depth += 1;
    else if (ch === ")" || ch === "]") depth = Math.max(0, depth - 1);
    else if (ch === "." && depth === 0 && (text[i + 1] === " " || i === text.length - 1)) {
      const preceding = text.slice(start, i);
      const endsAbbreviation = ABBREVIATIONS.some((a) => preceding.endsWith(a));
      if (!endsAbbreviation) {
        sentences.push(text.slice(start, i + 1).trim());
        start = i + 1;
      }
    }
  }
  const tail = text.slice(start).trim();
  if (tail.length > 0) {
    sentences.push(tail);
  }

  const kept: string[] = [];
  for (const sentence of sentences) {
    if (kept.length > 0 && [...kept, sentence].join(" ").length > softLimit) {
      break;
    }
    kept.push(sentence);
  }
  return kept.join(" ");
}

/**
 * "Phase 2 — Implementation (reframed project: does…)" carries a short label
 * and then a paragraph of detail. The label is what belongs in a status
 * column; the rest becomes the hover text.
 */
function phaseLabel(phase: string): string {
  const label = phase.split(/[.(]/)[0]?.trim() ?? phase;
  return label.length > 0 ? label : phase;
}

async function loadProjects(
  repoRoot: string,
  entries: {
    name: string;
    plan: string;
    notebook: string;
    tone?: string;
    what?: string;
  }[],
): Promise<Project[]> {
  return Promise.all(
    entries.map(async (entry) => {
      let markdown = "";
      try {
        markdown = await fs.readFile(path.resolve(repoRoot, entry.plan), "utf8");
      } catch {
        // A plan that has moved should be visible, not silently blank.
        return {
          name: entry.name,
          phase: "plan not found",
          phaseDetail: `Could not read ${entry.plan}`,
          what: entry.what ?? "",
          notebook: entry.notebook,
          tone: entry.tone ?? "draft",
        } satisfies Project;
      }

      const phaseDetail = sectionParagraph(markdown, "Current Phase");
      const objective = sectionParagraph(markdown, "Objective");
      const updated = /_Last updated:\s*(\d{4}-\d{2}-\d{2})/.exec(markdown);

      return {
        name: entry.name,
        phase: phaseLabel(phaseDetail),
        phaseDetail,
        what: entry.what ?? summarize(objective, 200),
        updated: updated?.[1],
        notebook: entry.notebook,
        tone: entry.tone ?? "draft",
      } satisfies Project;
    }),
  );
}

const RELEVANCE_ORDER: Record<Relevance, number> = {
  high: 0,
  medium: 1,
  low: 2,
};
const STATUS_ORDER: Record<PaperStatus, number> = {
  "to-read": 0,
  skimmed: 1,
  read: 2,
};

/**
 * Loads the site's three hand-kept data sources — the reading list, the
 * interactive pages, and blog front matter — and hands them to any page via
 * usePluginData("ocl-lab-data").
 */
export default async function labData(
  context: LoadContext,
  options: { blogDir?: string; routeBasePath?: string } = {},
): Promise<Plugin<LabData>> {
  const { siteDir } = context;
  const dataDir = path.join(siteDir, "data");
  const repoRoot = path.resolve(siteDir, "..");
  const blogDir = path.resolve(siteDir, options.blogDir ?? "blog");
  const routeBasePath = options.routeBasePath ?? "writing";

  return {
    name: "ocl-lab-data",

    async loadContent(): Promise<LabData> {
      const rawPapers =
        (await readYaml<Record<string, Omit<Paper, "id">>>(
          path.join(dataDir, "papers.yml"),
        )) ?? {};

      const papers: Paper[] = Object.entries(rawPapers)
        .map(([id, paper]) => ({
          ...paper,
          id,
          projects: paper.projects ?? [],
          verified: paper.verified ?? false,
        }))
        .sort(
          (a, b) =>
            RELEVANCE_ORDER[a.relevance] - RELEVANCE_ORDER[b.relevance] ||
            STATUS_ORDER[a.status] - STATUS_ORDER[b.status] ||
            b.year - a.year,
        );

      const rawBuilt =
        (await readYaml<{
          built: {
            name: string;
            title: string;
            topic: string;
            what: string;
            from?: string;
            url?: string;
            ratio?: number;
          }[];
        }>(path.join(dataDir, "built.yml")))?.built ?? [];

      const built: BuiltPage[] = rawBuilt.map((entry) => ({
        name: entry.name,
        title: entry.title,
        topic: entry.topic,
        what: entry.what.trim(),
        src: entry.url ?? `/demos/${entry.name}/`,
        external: Boolean(entry.url),
        origin: entry.url
          ? new URL(entry.url).host
          : (entry.from ?? "").split("/").slice(0, -1).join("/") || "repo root",
        ratio: entry.ratio ?? 1.6,
      }));

      const rawProjects =
        (await readYaml<{
          projects: {
            name: string;
            plan: string;
            notebook: string;
            tone?: string;
            what?: string;
          }[];
        }>(path.join(dataDir, "projects.yml")))?.projects ?? [];

      return {
        writing: await loadWriting(blogDir, routeBasePath),
        papers,
        built,
        projects: await loadProjects(repoRoot, rawProjects),
      };
    },

    async contentLoaded({ content, actions }) {
      actions.setGlobalData(content);
    },
  };
}
