import { computed, ref } from "vue";

// Professors and universities a student saves to compare later. Kept in this browser only
// (localStorage); everything works without it, the list just doesn't survive a reload.
export type Saved = {
  kind: "person" | "university";
  id: string;
  label: string;
  sub: string;
  universityId?: string | null;
};

const KEY = "atlas:shortlist";

function load(): Saved[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export const saved = ref<Saved[]>(load());
export const savedPeople = computed(() =>
  saved.value.filter((s) => s.kind === "person"),
);
export const savedUniversities = computed(() =>
  saved.value.filter((s) => s.kind === "university"),
);

function persist() {
  try {
    localStorage.setItem(KEY, JSON.stringify(saved.value));
  } catch {
    // storage blocked: the list lasts for this visit
  }
}

export function isSaved(kind: Saved["kind"], id: string): boolean {
  return saved.value.some((s) => s.kind === kind && s.id === id);
}

export function toggleSaved(item: Saved) {
  saved.value = isSaved(item.kind, item.id)
    ? saved.value.filter((s) => !(s.kind === item.kind && s.id === item.id))
    : [...saved.value, item];
  persist();
}

export function removeSaved(kind: Saved["kind"], id: string) {
  saved.value = saved.value.filter((s) => !(s.kind === kind && s.id === id));
  persist();
}
