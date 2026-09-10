import { themes as prismThemes } from "prism-react-renderer";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: "Open Concept Lab",
  tagline: "Experiments, writing, and things I built to see whether they work",
  favicon: "img/favicon.svg",

  future: {
    v4: true,
  },

  url: "https://rubix982.github.io",
  baseUrl: "/open-concept-lab/",

  organizationName: "Rubix982",
  projectName: "open-concept-lab",

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // KaTeX's own stylesheet is imported in src/css/custom.css, so it always
  // matches the installed renderer rather than a pinned CDN version.
  stylesheets: [
    "https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=IBM+Plex+Sans:ital,wght@0,400;0,450;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap",
  ],

  plugins: [
    [
      "./plugins/lab-data.ts",
      { blogDir: "blog", routeBasePath: "writing" },
    ],
  ],

  presets: [
    [
      "classic",
      {
        docs: {
          path: "notebook",
          routeBasePath: "notebook",
          sidebarPath: "./sidebars.ts",
          showLastUpdateTime: true,
          breadcrumbs: false,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          path: "blog",
          routeBasePath: "writing",
          blogTitle: "Writing",
          blogDescription:
            "Dated notes and essays from an ongoing research practice.",
          blogSidebarTitle: "All writing",
          blogSidebarCount: "ALL",
          showReadingTime: true,
          postsPerPage: 10,
          feedOptions: { type: null },
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          onInlineTags: "warn",
          onInlineAuthors: "warn",
          onUntruncatedBlogPosts: "warn",
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
        sitemap: {
          lastmod: "date",
          changefreq: null,
          priority: null,
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      // Light is the design; the OS preference does not override it. The
      // toggle still works for anyone who wants dark.
      defaultMode: "light",
      respectPrefersColorScheme: false,
    },
    metadata: [
      { name: "author", content: "Saif Ul Islam" },
      {
        name: "description",
        content:
          "Open Concept Lab — research writing on knowledge editing, interpretability, and what a model believes.",
      },
    ],
    navbar: {
      title: "Open Concept Lab",
      hideOnScroll: false,
      items: [
        { to: "/writing", label: "Writing", position: "left" },
        {
          type: "docSidebar",
          sidebarId: "notebookSidebar",
          position: "left",
          label: "Notebook",
        },
        { to: "/reading", label: "Reading", position: "left" },
        { to: "/built", label: "Built", position: "left" },
        { to: "/about", label: "About", position: "right" },
        {
          href: "https://github.com/Rubix982/open-concept-lab",
          label: "Source",
          position: "right",
        },
      ],
    },
    footer: {
      style: "light",
      links: [],
      copyright: `Written by Saif Ul Islam at Northeastern University. Nothing here is peer reviewed.`,
    },
    docs: {
      sidebar: { hideable: false, autoCollapseCategories: false },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 3,
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.nightOwl,
      additionalLanguages: ["bash", "python", "json", "yaml", "diff"],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
