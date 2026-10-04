<script setup lang="ts">
import { computed } from "vue";
import type { Area } from "@/api";
import { GROUP_ORDER, LINE_COLOR } from "@/lines";

const props = defineProps<{ areas: Area[]; modelValue: string[] }>();
const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

const groups = computed(() =>
  GROUP_ORDER.map((group) => ({
    group,
    color: LINE_COLOR[group],
    areas: props.areas.filter((a) => a.group === group).sort((a, b) => b.faculty - a.faculty),
  })).filter((g) => g.areas.length),
);

function toggle(area: string) {
  const selected = new Set(props.modelValue);
  if (selected.has(area)) selected.delete(area);
  else selected.add(area);
  emit("update:modelValue", [...selected]);
}
</script>

<template>
  <div class="picker">
    <div v-for="g in groups" :key="g.group" class="line" :style="{ '--c': g.color }">
      <h3 class="line-name">{{ g.group === "Interdisciplinary" ? "Interdisciplinary" : g.group }}</h3>
      <div class="stops">
        <button
          v-for="a in g.areas"
          :key="a.area"
          type="button"
          class="stop"
          :class="{ on: modelValue.includes(a.area) }"
          :aria-pressed="modelValue.includes(a.area)"
          :title="`${a.faculty} faculty, ${a.funded} with an active research grant`"
          @click="toggle(a.area)"
        >
          {{ a.name }}
        </button>
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
