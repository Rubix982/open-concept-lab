import { computed, ref } from "vue";
import type { Area, Funders } from "@/api";

// The area taxonomy, loaded once and shared by every component that labels an area.
export const areas = ref<Area[]>([]);

export const areaIndex = computed(() => new Map(areas.value.map((a) => [a.area, a])));

// Funder names, and which funders' grants are loaded for each country (from /explorer/funders).
export const funders = ref<Funders>({ names: { nsf: "NSF" }, by_country: { us: ["nsf"] } });

export function funderName(code: string | null | undefined): string {
  return (code && funders.value.names[code]) || (code ?? "").toUpperCase();
}

export function fundersFor(country: string | null | undefined): string[] {
  return funders.value.by_country[(country ?? "us").toLowerCase()] ?? [];
}
