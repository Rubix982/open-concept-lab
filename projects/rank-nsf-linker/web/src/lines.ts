// Each CSRankings area group is a "line" with one colour, used everywhere an area appears:
// the area picker, map dots and a professor's area tags.

export const LINE_COLOR: Record<string, string> = {
  AI: "var(--line-ai)",
  Systems: "var(--line-systems)",
  Theory: "var(--line-theory)",
  Interdisciplinary: "var(--line-inter)",
};

// Mapbox paint properties cannot read CSS variables, so the map gets the raw values.
export const LINE_HEX: Record<string, string> = {
  AI: "#2F6FDB",
  Systems: "#1E9E6A",
  Theory: "#8E4FD1",
  Interdisciplinary: "#C98A0C",
};

export const INK_HEX = "#1D2A3A";

export const GROUP_ORDER = ["AI", "Systems", "Theory", "Interdisciplinary"];

export function formatMoney(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1)}M`;
  if (n >= 1_000) return `$${Math.round(n / 1_000)}k`;
  return `$${n}`;
}

export function formatYear(date: string | null): string {
  return date ? date.slice(0, 4) : "";
}
