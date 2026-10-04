import { computed, ref, watch } from "vue";
import type { Area } from "@/api";

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
