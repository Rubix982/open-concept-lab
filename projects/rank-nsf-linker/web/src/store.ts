import { computed, ref, watch } from "vue";
import type { Area, Funders } from "@/api";

// The area taxonomy, loaded once and shared by every component that labels an area.
export const areas = ref<Area[]>([]);

export const areaIndex = computed(() => new Map(areas.value.map((a) => [a.area, a])));

// The student's nationality (ISO alpha-2, upper case), for scholarship eligibility.
// Remembered in this browser only.
function readNationality(): string {
  try {
    return localStorage.getItem("nationality") ?? "";
  } catch {
    return "";
  }
}
export const nationality = ref(readNationality());
watch(nationality, (v) => {
  try {
    localStorage.setItem("nationality", v);
  } catch {
    // private mode or blocked storage: keep it for this visit only
  }
});

// Funder names, and which funders' grants are loaded for each country (from /explorer/funders).
export const funders = ref<Funders>({ names: { nsf: "NSF" }, by_country: { us: ["nsf"] } });

export function funderName(code: string | null | undefined): string {
  return (code && funders.value.names[code]) || (code ?? "").toUpperCase();
}

export function fundersFor(country: string | null | undefined): string[] {
  return funders.value.by_country[(country ?? "us").toLowerCase()] ?? [];
}
