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

      return {
        writing: await loadWriting(blogDir, routeBasePath),
        papers,
        built,
      };
    },

    async contentLoaded({ content, actions }) {
      actions.setGlobalData(content);
    },
  };
}
