import { computed, ref } from "vue";
import type { Area, Funders } from "@/api";

// The area taxonomy, loaded once and shared by every component that labels an area.
export const areas = ref<Area[]>([]);

export const areaIndex = computed(
  () => new Map(areas.value.map((a) => [a.area, a])),
);

// Funder names, and which funders' grants are loaded for each country (from /explorer/funders).
export const funders = ref<Funders>({
  names: { nsf: "NSF" },
  by_country: { us: ["nsf"] },
});

export function funderName(code: string | null | undefined): string {
  return (code && funders.value.names[code]) || (code ?? "").toUpperCase();
}

// What a "new lab" grant is called, for a tag or a sentence.
export function newLabLabel(funder: string, scheme: string | null): string {
  switch (funder) {
    case "nsf":
      return "NSF CAREER award";
    case "erc":
      return "ERC Starting Grant";
    case "arc":
      return "ARC early-career award (DECRA)";
    case "nih":
      return "NIH new-faculty grant (R00)";
    case "kaken":
      return "KAKEN early-career grant";
    case "anr":
      return "ANR young researcher grant";
    case "ukri":
      return "UKRI new investigator award";
    case "nserc":
      return "NSERC Discovery Launch Supplement";
    default:
      return `${funderName(funder)} ${scheme ?? "early-career grant"}`;
  }
}

export function fundersFor(country: string | null | undefined): string[] {
  return country ? (funders.value.by_country[country.toLowerCase()] ?? []) : [];
}
