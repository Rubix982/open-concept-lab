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
    case "nwo":
      return "NWO Vidi grant";
    case "nsfc":
      return "NSFC Young Scientists Fund grant";
    case "cihr":
      return "CIHR new-investigator grant";
    case "anid":
      return "FONDECYT initiation grant (Chile)";
    case "ncn":
      return scheme?.startsWith("SONATA BIS")
        ? "NCN SONATA BIS grant (new research team)"
        : "NCN SONATA grant (early career)";
    case "fapesp":
      return "FAPESP Young Investigator grant";
    case "sfi":
      return "Research Ireland Starting Investigator grant";
    case "wellcome":
      return scheme ?? "Wellcome early-career award";
    case "nhmrc":
      return "NHMRC Emerging Leadership grant";
    case "isf":
      return "ISF new-faculty grant";
    case "dff":
      return "DFF Sapere Aude research leader grant";
    case "fwf":
      return scheme === "FWF START Awards"
        ? "FWF START award"
        : "FWF young research group";
    default:
      return `${funderName(funder)} ${scheme ?? "early-career grant"}`;
  }
}

export function fundersFor(country: string | null | undefined): string[] {
  return country ? (funders.value.by_country[country.toLowerCase()] ?? []) : [];
}
