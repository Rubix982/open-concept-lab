<script setup lang="ts">
import { computed, ref } from "vue";
import type { Area } from "@/api";
import { GROUP_ORDER, LINE_COLOR } from "@/lines";

const props = defineProps<{ areas: Area[]; modelValue: string[] }>();
const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

// OpenAlex areas are subfields: grouped under their field, the 8 with most people shown first.
const SHOWN = 8;
const opened = ref(new Set<string>());
const groups = computed(() =>
  GROUP_ORDER.map((group) => {
    const areas = props.areas
      .filter((a) => a.group === group)
      .sort((a, b) => b.faculty - a.faculty);
    const byField = new Map<string, Area[]>();
    for (const a of areas)
      byField.set(a.field ?? "", [...(byField.get(a.field ?? "") ?? []), a]);
    const fields = [...byField.entries()]
      .map(([field, list]) => ({
        field,
        list,
        total: list.reduce((n, a) => n + a.faculty, 0),
      }))
      .sort((a, b) =>
        a.field === "" ? -1 : b.field === "" ? 1 : b.total - a.total,
      );
    return { group, color: LINE_COLOR[group], fields };
  }).filter((g) => g.fields.length),
);

// The first 8, plus any selected beyond them, unless the field is opened. Computer science
// areas (no field) are always listed in full.
function shown(group: string, field: string, list: Area[]): Area[] {
  if (!field || opened.value.has(`${group}|${field}`) || list.length <= SHOWN)
    return list;
  return [
    ...list.slice(0, SHOWN),
    ...list.slice(SHOWN).filter((a) => props.modelValue.includes(a.area)),
  ];
}

function toggleMore(group: string, field: string) {
  const key = `${group}|${field}`;
  const next = new Set(opened.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  opened.value = next;
}

function toggle(area: string) {
  const selected = new Set(props.modelValue);
  if (selected.has(area)) selected.delete(area);
  else selected.add(area);
  emit("update:modelValue", [...selected]);
}
</script>

<template>
  <div class="picker">
    <div
      v-for="g in groups"
      :key="g.group"
      class="line"
      :style="{ '--c': g.color }"
    >
      <h3 class="line-name">{{ g.group }}</h3>
      <div v-for="f in g.fields" :key="f.field" class="field">
        <p v-if="f.field" class="field-name">{{ f.field }}</p>
        <div class="stops">
          <button
            v-for="a in shown(g.group, f.field, f.list)"
            :key="a.area"
            type="button"
            class="stop"
            :class="{ on: modelValue.includes(a.area) }"
            :aria-pressed="modelValue.includes(a.area)"
            :title="`${a.faculty} faculty and researchers, ${a.funded} with an active research grant`"
            @click="toggle(a.area)"
          >
            {{ a.name }}
          </button>
          <button
            v-if="f.field && f.list.length > SHOWN"
            type="button"
            class="more"
            :aria-expanded="opened.has(`${g.group}|${f.field}`)"
            @click="toggleMore(g.group, f.field)"
          >
            {{
              opened.has(`${g.group}|${f.field}`)
                ? "Fewer"
                : `+${f.list.length - SHOWN} more`
            }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.picker {
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

.field + .field {
  margin-top: 6px;
}

.field-name {
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink-soft);
  margin: 2px 0 3px;
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

/* On phones each line is one row that scrolls sideways. */
@media (max-width: 900px) {
  .stops {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 4px;
    scrollbar-width: thin;
  }
  .stop {
    white-space: nowrap;
  }
}
</style>
