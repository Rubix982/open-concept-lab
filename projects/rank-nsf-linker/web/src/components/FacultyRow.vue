<script setup lang="ts">
import { computed } from "vue";
import type { Faculty } from "@/api";
import { LINE_COLOR, formatMoney } from "@/lines";
import { areaIndex } from "@/store";

const props = defineProps<{ person: Faculty; showUniversity?: boolean; selectedAreas: string[] }>();
defineEmits<{ open: [name: string] }>();

// Selected areas first, then the professor's strongest; at most three.
const tags = computed(() => {
  const ordered = [
    ...props.person.areas.filter((a) => props.selectedAreas.includes(a)),
    ...props.person.areas.filter((a) => !props.selectedAreas.includes(a)),
  ];
  return ordered.slice(0, 3).map((a) => {
    const info = areaIndex.value.get(a);
    return { area: a, name: info?.name ?? a, color: LINE_COLOR[info?.group ?? ""] ?? "var(--ink-soft)" };
  });
});

// CSRankings disambiguates namesakes with a number ("Wei Wang 0001"); students don't need it.
const displayName = computed(() => props.person.name.replace(/\s+\d{4}$/, ""));
</script>

<template>
  <li class="row">
    <button type="button" class="hit" @click="$emit('open', person.name)">
      <span class="name">{{ displayName }}</span>
      <span v-if="showUniversity" class="uni">{{ person.university }}</span>
    </button>
    <div class="tags">
      <span v-for="t in tags" :key="t.area" class="tag" :style="{ '--c': t.color }">{{ t.name }}</span>
    </div>
    <p v-if="person.match" class="match">
      <span class="kind">{{ person.match.kind === "paper" ? "Paper" : "NSF grant" }}<template v-if="person.match.year">, {{ person.match.year }}</template>:</span>
      {{ person.match.title }}
    </p>
    <p class="funding">
      <span class="fund-dot" :class="{ on: person.active_awards > 0 }" aria-hidden="true"></span>
      <span v-if="person.active_awards > 0">
        {{ person.active_awards }} active NSF {{ person.active_awards === 1 ? "grant" : "grants" }},
        <span class="num">{{ formatMoney(person.active_funding) }}</span>
      </span>
      <span v-else-if="person.total_awards > 0">No active NSF grant ({{ person.total_awards }} past)</span>
      <span v-else>No NSF grants on record</span>
    </p>
  </li>
</template>

<style scoped>
.row {
  list-style: none;
  padding: 12px 0 13px;
  border-bottom: 1px solid var(--rule);
}

.hit {
  display: block;
  width: 100%;
  text-align: left;
  border: 0;
  background: none;
  padding: 0;
}

.name {
  display: block;
  font-size: var(--t-md);
  font-weight: 800;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
}

.hit:hover .name {
  text-decoration-color: var(--ink);
}

.uni {
  display: block;
  color: var(--ink-soft);
  font-size: var(--t-xs);
  margin-top: 1px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  margin-top: 6px;
}

.tag {
  font-size: var(--t-xs);
  font-weight: 600;
  color: var(--ink-soft);
  border-left: 3px solid var(--c);
  padding-left: 6px;
  line-height: 1.2;
}

.match {
  margin-top: 7px;
  font-size: var(--t-xs);
  line-height: 1.4;
  color: var(--ink);
}

.kind {
  font-weight: 700;
}

.funding {
  margin-top: 7px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
</style>
