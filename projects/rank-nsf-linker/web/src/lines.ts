// Each CSRankings area group is a "line" with one colour, used everywhere an area appears:
// the area picker, map dots and a professor's area tags.

export const LINE_COLOR: Record<string, string> = {
  AI: "var(--line-ai)",
  Systems: "var(--line-systems)",
  Theory: "var(--line-theory)",
  Interdisciplinary: "var(--line-inter)",
  Sciences: "var(--line-sciences)",
  Engineering: "var(--line-engineering)",
  Medicine: "var(--line-medicine)",
  "Social sciences & humanities": "var(--line-social)",
};

// Mapbox paint properties cannot read CSS variables, so the map gets the raw values.
export const LINE_HEX: Record<string, string> = {
  AI: "#2F6FDB",
  Systems: "#1E9E6A",
  Theory: "#8E4FD1",
  Interdisciplinary: "#C98A0C",
  Sciences: "#0E8A8A",
  Engineering: "#B8452F",
  Medicine: "#A8357A",
  "Social sciences & humanities": "#6B7A1C",
};

export const INK_HEX = "#1D2A3A";

export const GROUP_ORDER = [
  "AI",
  "Systems",
  "Theory",
  "Interdisciplinary",
  "Sciences",
  "Engineering",
  "Medicine",
  "Social sciences & humanities",
];

// "$2.6M", "A$7.8M", "NZ$853K", "€1.2M"
export function formatMoney(n: number, currency = "USD"): string {
  try {
    return new Intl.NumberFormat("en", {
      style: "currency",
      currency: currency || "USD",
      notation: "compact",
      maximumFractionDigits: n >= 10_000_000 ? 0 : 1,
    }).format(n);
  } catch {
    return `${Math.round(n).toLocaleString("en")} ${currency}`;
  }
}

export function formatYear(date: string | null): string {
  return date ? date.slice(0, 4) : "";
}

// Links from data (homepages, grant and paper pages) go through this: only http(s) URLs are
// rendered, so a "javascript:" value in the source data can't run. Bare domains get https://.
export function webUrl(url: string | null | undefined): string | undefined {
  const u = (url ?? "").trim();
  if (!u) return undefined;
  if (/^https?:\/\//i.test(u)) return u;
  if (/^[a-z][a-z0-9+.-]*:/i.test(u)) return undefined; // another scheme: javascript:, data:, ...
  return `https://${u.replace(/^\/+/, "")}`;
}

// Grants, as the Funding tab and a university's page show them
export function niceName(s: string): string {
  // UKRI lists institutions in capitals; KAKEN adds the Japanese name after " | ".
  const first = s.split(" | ")[0];
  // Only longer all-caps names: "OHSU" and "MIT" stay as they are.
  return first === first.toUpperCase() && first.includes(" ")
    ? first
        .toLowerCase()
        // capitalise words, not letters after an apostrophe ("Children's", not "Children'S")
        .replace(/(^|[\s(\-/&,.])(\w)/g, (_, sep, c) => sep + c.toUpperCase())
    : first;
}
// a profile name without the year DBLP adds to tell namesakes apart ("Wei Wang 0001")
export function short(name: string) {
  return name.replace(/\s+\d{4}$/, "");
}
export function grantYears(g: { starts: string | null; ends: string | null }) {
  return [formatYear(g.starts), formatYear(g.ends)].filter(Boolean).join("–");
}
// "≈ $1.2M": amounts from 42 funders in one currency, at fixed approximate rates (server/currency.go)
export function approxUSD(
  v: number | null | undefined,
  currency?: string | null,
) {
  if (v == null || currency === "USD") return "";
  return `≈ ${formatMoney(v, "USD")}`;
}
// Titles some funders publish only in their own language
export function titleLanguage(t: string): string {
  if (/[\uac00-\ud7a3]/.test(t)) return "Title in Korean";
  if (/[\u3040-\u30ff]/.test(t)) return "Title in Japanese";
  if (/[\u3400-\u9fff]/.test(t)) return "Title in Chinese";
  return "";
}
export const KIND_LABEL = {
  new_lab: "New lab",
  training: "Funds PhD students",
} as const;
// A person's name as some funders send it ("ROBERT Frank Paulson", "JANE DOE"): words in capitals
// become "Robert"; initials ("W", "J.") and short particles stay as they are.
export function personName(name: string | null | undefined): string {
  return (name ?? "").replace(/\p{Lu}{2,}[\p{Lu}'-]*/gu, (w) =>
    w.length <= 2
      ? w
      : // "SEO-YEON" -> "Seo-Yeon", "O'BRIEN" -> "O'Brien"
        w
          .toLowerCase()
          .replace(/(^|[-'])(\p{L})/gu, (_, sep, c) => sep + c.toUpperCase()),
  );
}
