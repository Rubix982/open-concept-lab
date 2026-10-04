<script setup lang="ts">
import { computed } from "vue";
import type { Grant } from "@/api";
import { formatMoney, formatYear, webUrl } from "@/lines";
import { funderName } from "@/store";

const props = defineProps<{ grant: Grant }>();
defineEmits<{ openPerson: [name: string, universityId: string | null] }>();

const status = computed(() => {
  const end = props.grant.ends
    ? new Date(props.grant.ends).toLocaleDateString("en-US", { month: "short", year: "numeric" })
    : "";
  return props.grant.active ? `Active until ${end}` : `Ended ${end}`;
});
</script>

<template>
  <li class="grant" :class="{ active: grant.active }">
    <a :href="webUrl(grant.url)" target="_blank" rel="noopener" class="title">{{ grant.title }}</a>
    <p class="meta">
      <strong>{{ status }}</strong>, {{ funderName(grant.funder) }},
      <span class="num">{{ formatMoney(grant.amount, grant.currency) }}</span>,
      started {{ formatYear(grant.starts) }}
    </p>
    <p v-if="grant.abstract" class="abstract">{{ grant.abstract }}&hellip;</p>
    <ul class="people">
      <li v-for="p in grant.people" :key="p.name">
        <button type="button" @click="$emit('openPerson', p.name, p.university_id)">
          {{ p.name.replace(/\s+\d{4}$/, "") }}
        </button>
        <span class="uni">{{ p.university }}</span>
      </li>
    </ul>
  </li>
</template>

<style scoped>
.grant {
  list-style: none;
  padding: 12px 0 13px;
  border-bottom: 1px solid var(--rule);
}

.grant.active {
  border-left: 4px solid var(--ink);
  padding-left: 11px;
}

.title {
  font-weight: 700;
  text-decoration: none;
  line-height: 1.35;
}

.title:hover {
  text-decoration: underline;
}

.meta {
  margin-top: 4px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.meta strong {
  color: var(--ink);
}

.abstract {
  margin-top: 6px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.people {
  margin: 8px 0 0;
  padding: 0;
  display: grid;
  gap: 3px;
}

.people li {
  list-style: none;
  font-size: var(--t-xs);
}

.people button {
  border: 0;
  background: none;
  padding: 0;
  font-weight: 700;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
}

.people button:hover {
  text-decoration-color: var(--ink);
}

.uni {
  color: var(--ink-soft);
  margin-left: 6px;
}
</style>
