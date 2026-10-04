<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { api, type Award, type Faculty, type Paper } from "@/api";
import { LINE_COLOR, formatMoney, formatYear } from "@/lines";
import { areaIndex } from "@/store";

const props = defineProps<{ name: string; backLabel: string }>();
defineEmits<{ back: [] }>();

const person = ref<Faculty | null>(null);
const awards = ref<Award[]>([]);
const papers = ref<Paper[] | null>(null);
const dblpUrl = ref("");
const error = ref("");

watch(
  () => props.name,
  async (name) => {
    person.value = null;
    papers.value = null;
    error.value = "";
    try {
      const profile = await api.profile(name);
      person.value = profile.faculty;
      awards.value = profile.awards;
    } catch (e) {
      error.value = (e as Error).message;
      return;
    }
    api
      .papers(name)
      .then((r) => {
        papers.value = r.papers;
        dblpUrl.value = r.dblp_url;
      })
      .catch(() => (papers.value = []));
  },
  { immediate: true },
);

const displayName = computed(() => props.name.replace(/\s+\d{4}$/, ""));

const areaList = computed(() =>
  (person.value?.areas ?? []).map((a) => {
    const info = areaIndex.value.get(a);
    return {
      area: a,
      name: info?.name ?? a,
      color: LINE_COLOR[info?.group ?? ""] ?? "var(--ink-soft)",
      pubs: person.value?.area_pubs[a] ?? 0,
    };
  }),
);

const activeAwards = computed(() => awards.value.filter((a) => a.active));
const fundedUntil = computed(() => {
  const ends = activeAwards.value.map((a) => a.ends ?? "").sort();
  return ends[ends.length - 1] ?? "";
});

function untilLabel(date: string | null): string {
  if (!date) return "";
  return new Date(date).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}
</script>

<template>
  <article class="prof">
    <button type="button" class="back" @click="$emit('back')">Back to {{ backLabel }}</button>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="person">
      <header>
        <h2>{{ displayName }}</h2>
        <p class="uni">{{ person.university }}</p>
        <p class="links">
          <a v-if="person.homepage" :href="person.homepage" target="_blank" rel="noopener">Homepage</a>
          <a
            v-if="person.scholar_id"
            :href="`https://scholar.google.com/citations?user=${encodeURIComponent(person.scholar_id)}`"
            target="_blank"
            rel="noopener"
            >Google Scholar</a
          >
          <a v-if="dblpUrl" :href="dblpUrl" target="_blank" rel="noopener">DBLP</a>
        </p>
      </header>

      <section>
        <h3>Research areas</h3>
        <p class="hint">Papers at top venues in the last 10 years, from CSRankings</p>
        <ul class="areas">
          <li v-for="a in areaList" :key="a.area" :style="{ '--c': a.color }">
            <span class="area-name">{{ a.name }}</span>
            <span class="num">{{ a.pubs }} {{ a.pubs === 1 ? "paper" : "papers" }}</span>
          </li>
        </ul>
      </section>

      <section>
        <h3>Funding</h3>
        <p v-if="activeAwards.length" class="funding-note">
          <span class="fund-dot on" aria-hidden="true"></span>
          {{ activeAwards.length }} active NSF {{ activeAwards.length === 1 ? "grant" : "grants" }}, running until
          {{ untilLabel(fundedUntil) }}. Grants like these usually pay PhD students as research assistants, so
          it's worth asking about openings when you write.
        </p>
        <p v-else class="funding-note">
          <span class="fund-dot" aria-hidden="true"></span>
          No active NSF grant on record. They may be funded by industry or other agencies, which this data
          doesn't cover, so ask.
        </p>
      </section>

      <section>
        <h3>Recent papers</h3>
        <p v-if="papers === null" class="hint">Loading papers</p>
        <p v-else-if="!papers.length" class="hint">No recent papers loaded for this professor yet.</p>
        <ol v-else class="papers">
          <li v-for="p in papers" :key="p.title">
            <a v-if="p.url" :href="p.url" target="_blank" rel="noopener">{{ p.title }}</a>
            <span v-else>{{ p.title }}</span>
            <span class="meta">{{ p.venue }} {{ p.year }}</span>
          </li>
        </ol>
      </section>

      <section>
        <h3>NSF grants</h3>
        <p v-if="!awards.length" class="hint">No NSF grants linked to this professor.</p>
        <ol class="awards">
          <li v-for="a in awards" :key="a.id" :class="{ active: a.active }">
            <a :href="a.url" target="_blank" rel="noopener" class="award-title">{{ a.title }}</a>
            <p class="meta">
              <span class="num">{{ formatMoney(a.amount) }}</span>,
              {{ formatYear(a.starts) }}&ndash;{{ formatYear(a.ends) }}<template v-if="a.role">, {{ a.role }}</template>
              <strong v-if="a.active">, active</strong>
            </p>
            <details v-if="a.abstract">
              <summary>Abstract</summary>
              <p>{{ a.abstract }}&hellip;</p>
            </details>
          </li>
        </ol>
      </section>
    </template>
  </article>
</template>

<style scoped>
.prof {
  display: grid;
  gap: 22px;
}

.back {
  justify-self: start;
  border: 0;
  background: none;
  padding: 0;
  font-weight: 700;
  font-size: var(--t-xs);
  color: var(--ink-soft);
  text-decoration: underline;
  text-underline-offset: 3px;
}

h2 {
  font-size: var(--t-xl);
  font-weight: 800;
  letter-spacing: -0.01em;
}

.uni {
  margin-top: 4px;
  color: var(--ink-soft);
}

.links {
  display: flex;
  gap: 16px;
  margin-top: 10px;
  font-weight: 700;
  font-size: var(--t-xs);
}

h3 {
  font-size: var(--t-sm);
  font-weight: 800;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 8px;
}

.hint {
  font-size: var(--t-xs);
  color: var(--ink-faint);
  margin-bottom: 6px;
}

.areas {
  list-style: none;
  margin: 0;
  padding: 0;
}

.areas li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0 4px 9px;
  border-left: 4px solid var(--c);
  margin-bottom: 3px;
}

.funding-note {
  display: flex;
  gap: 9px;
  align-items: baseline;
}

.papers,
.awards {
  list-style: none;
  margin: 0;
  padding: 0;
}

.papers li,
.awards li {
  padding: 8px 0;
  border-bottom: 1px solid var(--rule);
}

.papers a,
.award-title {
  font-weight: 600;
  text-decoration: none;
}

.papers a:hover,
.award-title:hover {
  text-decoration: underline;
}

.meta {
  display: block;
  margin-top: 2px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.awards li.active {
  border-left: 4px solid var(--ink);
  padding-left: 10px;
}

details {
  margin-top: 4px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

summary {
  cursor: pointer;
  font-weight: 700;
}

details p {
  margin-top: 4px;
  max-width: 62ch;
}

.error {
  color: var(--danger);
}
</style>
