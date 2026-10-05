<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Area } from "@/api";
import { LINE_COLOR } from "@/lines";

const props = defineProps<{ areas: Area[]; modelValue: string[] }>();
const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

// 234 areas are too many to show at once. One domain at a time; outside computer science, a list
// of fields and then one field's subfields; and a search box across all of them.
const DOMAINS = [
  {
    id: "cs",
    label: "Computer science",
    groups: ["AI", "Systems", "Theory", "Interdisciplinary"],
  },
  { id: "sci", label: "Sciences", groups: ["Sciences"] },
  { id: "eng", label: "Engineering", groups: ["Engineering"] },
  { id: "med", label: "Medicine", groups: ["Medicine"] },
  {
    id: "soc",
    label: "Social sciences & humanities",
    groups: ["Social sciences & humanities"],
  },
];
const domainOf = (a: Area) =>
  DOMAINS.find((d) => d.groups.includes(a.group))?.id ?? "cs";

const selected = computed(() => new Set(props.modelValue));
const query = ref("");
const firstPicked = props.areas.find((a) => selected.value.has(a.area));
const domain = ref(firstPicked ? domainOf(firstPicked) : "cs");
const field = ref<string | null>(firstPicked?.field ?? null);

const byPeople = (a: Area, b: Area) => b.faculty - a.faculty;

// Computer science: its four lines, as before.
const csLines = computed(() =>
  DOMAINS[0].groups
    .map((group) => ({
      group,
      color: LINE_COLOR[group],
      areas: props.areas.filter((a) => a.group === group).sort(byPeople),
    }))
    .filter((l) => l.areas.length),
);

// Other domains: their fields, largest first, and the chosen field's subfields.
const fields = computed(() => {
  const m = new Map<string, Area[]>();
  for (const a of props.areas) {
    if (domainOf(a) !== domain.value || !a.field) continue;
    m.set(a.field, [...(m.get(a.field) ?? []), a]);
  }
  return [...m.entries()]
    .map(([name, list]) => ({
      name,
      list: list.sort(byPeople),
      people: list.reduce((n, a) => n + a.faculty, 0),
      picked: list.filter((a) => selected.value.has(a.area)).length,
    }))
    .sort((a, b) => b.people - a.people);
});
watch(
  [domain, fields],
  () => {
    if (
      domain.value !== "cs" &&
      !fields.value.some((f) => f.name === field.value)
    ) {
      field.value = fields.value[0]?.name ?? null;
    }
  },
  { immediate: true },
);
const current = computed(
  () => fields.value.find((f) => f.name === field.value) ?? null,
);
// A long field (Medicine has 32 subfields) shows its 12 largest first, plus any already chosen.
const FIRST = 12;
const showAll = ref(false);
watch(field, () => (showAll.value = false));
const currentShown = computed(() => {
  const list = current.value?.list ?? [];
  if (showAll.value || list.length <= FIRST) return list;
  return [
    ...list.slice(0, FIRST),
    ...list.slice(FIRST).filter((a) => selected.value.has(a.area)),
  ];
});
const domainColor = computed(
  () =>
    LINE_COLOR[DOMAINS.find((d) => d.id === domain.value)?.groups[0] ?? ""] ??
    "var(--ink)",
);
const pickedIn = (id: string) =>
  props.areas.filter((a) => domainOf(a) === id && selected.value.has(a.area))
    .length;

// Search across every area by name or field.
const results = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (q.length < 2) return [];
  return props.areas
    .filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        (a.field ?? "").toLowerCase().includes(q),
    )
    .sort(byPeople)
    .slice(0, 24);
});

function toggle(area: string) {
  const next = new Set(props.modelValue);
  if (next.has(area)) next.delete(area);
  else next.add(area);
  emit("update:modelValue", [...next]);
}

// "All of <field>": every subfield of the field on, or all of them off.
function toggleField(list: Area[]) {
  const next = new Set(props.modelValue);
  const all = list.every((a) => next.has(a.area));
  for (const a of list) {
    if (all) next.delete(a.area);
    else next.add(a.area);
  }
  emit("update:modelValue", [...next]);
}
const colorOf = (a: Area) => LINE_COLOR[a.group] ?? "var(--ink)";
const tip = (a: Area) =>
  `${a.faculty} faculty and researchers, ${a.funded} with an active research grant`;
</script>

<template>
  <div class="picker">
    <label class="find">
      <span class="visually-hidden">Find an area</span>
      <input
        v-model="query"
        type="search"
        placeholder="Find an area, e.g. cardiology or robotics"
        autocomplete="off"
      />
    </label>

    <template v-if="query.trim().length >= 2">
      <p v-if="!results.length" class="hint">
        No area matches “{{ query.trim() }}”. Try a broader word.
      </p>
      <div v-else class="stops">
        <button
          v-for="a in results"
          :key="a.area"
          type="button"
          class="stop"
          :class="{ on: selected.has(a.area) }"
          :style="{ '--c': colorOf(a) }"
          :aria-pressed="selected.has(a.area)"
          :title="tip(a)"
          @click="toggle(a.area)"
        >
          {{ a.name }}<span v-if="a.field" class="in"> · {{ a.field }}</span>
        </button>
      </div>
    </template>

    <template v-else>
      <div class="domains" role="tablist" aria-label="Domain">
        <button
          v-for="d in DOMAINS"
          :key="d.id"
          type="button"
          role="tab"
          :aria-selected="domain === d.id"
          :class="{ on: domain === d.id }"
          @click="domain = d.id"
        >
          {{ d.label
          }}<span v-if="pickedIn(d.id)" class="count">{{
            pickedIn(d.id)
          }}</span>
        </button>
      </div>

      <div v-if="domain === 'cs'" class="cs">
        <div
          v-for="l in csLines"
          :key="l.group"
          class="line"
          :style="{ '--c': l.color }"
        >
          <h3 class="line-name">{{ l.group }}</h3>
          <div class="stops">
            <button
              v-for="a in l.areas"
              :key="a.area"
              type="button"
              class="stop"
              :class="{ on: selected.has(a.area) }"
              :aria-pressed="selected.has(a.area)"
              :title="tip(a)"
              @click="toggle(a.area)"
            >
              {{ a.name }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="split" :style="{ '--c': domainColor }">
        <ul class="fields" aria-label="Fields">
          <li v-for="f in fields" :key="f.name">
            <button
              type="button"
              :class="{ on: field === f.name }"
              :aria-current="field === f.name"
              @click="field = f.name"
            >
              <span>{{ f.name }}</span>
              <span v-if="f.picked" class="count">{{ f.picked }}</span>
            </button>
          </li>
        </ul>
        <div v-if="current" class="subs">
          <div class="stops">
            <button
              type="button"
              class="stop all"
              :class="{ on: current.list.every((a) => selected.has(a.area)) }"
              @click="toggleField(current.list)"
            >
              All of {{ current.name }}
            </button>
            <button
              v-for="a in currentShown"
              :key="a.area"
              type="button"
              class="stop"
              :class="{ on: selected.has(a.area) }"
              :aria-pressed="selected.has(a.area)"
              :title="tip(a)"
              @click="toggle(a.area)"
            >
              {{ a.name }}
            </button>
            <button
              v-if="current.list.length > FIRST"
              type="button"
              class="more"
              :aria-expanded="showAll"
              @click="showAll = !showAll"
            >
              {{ showAll ? "Fewer" : `Show all ${current.list.length}` }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.picker {
  display: grid;
  gap: 12px;
}

.find input {
  width: 100%;
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--radius-box);
  padding: 7px 10px 6px;
  font: inherit;
  font-size: var(--t-sm);
  color: var(--ink);
  background: var(--surface);
}

.find input:focus-visible {
  outline: 3px solid var(--line-ai);
  outline-offset: 0;
}

.hint {
  font-size: var(--t-xs);
  color: var(--ink-faint);
}

.domains {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  border-bottom: 2px solid var(--ink);
}

.domains button {
  border: 0;
  background: none;
  padding: 6px 10px 4px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink-soft);
  border-radius: var(--radius-box) var(--radius-box) 0 0;
  cursor: pointer;
}

.domains button.on {
  background: var(--ink);
  color: #fff;
}

.count {
  display: inline-block;
  margin-left: 6px;
  min-width: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--line-ai);
  color: #fff;
  font-size: 0.7rem;
  text-align: center;
}

.cs {
  display: grid;
  gap: 10px;
}

.line {
  position: relative;
  padding-left: 18px;
}

/* The line itself: a thick coloured rule the stops hang off. */
.line::before {
  content: "";
  position: absolute;
  left: 4px;
  top: 4px;
  bottom: 4px;
  width: 4px;
  border-radius: 2px;
  background: var(--c);
}

.line-name {
  font-size: var(--t-xs);
  font-weight: 800;
  color: var(--c);
  margin-bottom: 4px;
}

.split {
  display: grid;
  grid-template-columns: minmax(170px, 230px) 1fr;
  gap: 14px;
  align-items: start;
}

.fields {
  margin: 0;
  padding: 0;
  list-style: none;
  border-left: 4px solid var(--c);
}

.fields button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  border: 0;
  background: none;
  padding: 5px 10px 4px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 600;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.fields button.on {
  background: var(--paper);
  font-weight: 800;
  color: var(--c);
}

.stops {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.stop {
  border: 1.5px solid var(--rule-strong);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 3px 9px 2px;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--ink);
  cursor: pointer;
  transition:
    background 120ms,
    border-color 120ms,
    color 120ms;
}

.stop:hover {
  border-color: var(--c);
}

.stop.on {
  background: var(--c);
  border-color: var(--c);
  color: #fff;
}

.more {
  border: 0;
  background: none;
  padding: 4px 6px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink-soft);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.stop.all {
  border-style: dashed;
}

.in {
  font-weight: 400;
  opacity: 0.75;
}

@media (max-width: 700px) {
  .split {
    grid-template-columns: 1fr;
  }
  .fields {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    border-left: 0;
    border-bottom: 3px solid var(--c);
  }
  .fields button {
    white-space: nowrap;
  }
}
</style>
