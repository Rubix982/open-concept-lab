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
