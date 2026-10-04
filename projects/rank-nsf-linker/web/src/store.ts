import { computed, ref } from "vue";
import type { Area } from "@/api";

// The area taxonomy, loaded once and shared by every component that labels an area.
export const areas = ref<Area[]>([]);

export const areaIndex = computed(() => new Map(areas.value.map((a) => [a.area, a])));
