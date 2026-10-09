<script setup lang="ts">
import { computed, ref, watch } from "vue";
import LoadingRows from "@/components/LoadingRows.vue";
import {
  api,
  type Award,
  type Collaborator,
  type Faculty,
  type Paper,
  type SimilarPerson,
} from "@/api";
import {
  LINE_COLOR,
  formatMoney,
  formatYear,
  grantTitle,
  webUrl,
} from "@/lines";
import {
  areaIndex,
  funderName,
  fundersFor,
  newLabLabel,
  showGrant,
} from "@/store";
import { countryName } from "@/countries";
import { isSaved, toggleSaved } from "@/shortlist";

const props = defineProps<{ name: string; backLabel: string; goal?: string }>();
const emit = defineEmits<{
  back: [];
  open: [name: string];
  university: [id: string];
}>();

const person = ref<Faculty | null>(null);
const awards = ref<Award[]>([]);
const collaborators = ref<Collaborator[]>([]);
const previously = ref<string[]>([]);
const topics = ref<{ topic: string; papers: number }[]>([]);
const similar = ref<SimilarPerson[] | null>(null);
const papers = ref<Paper[] | null>(null);
const matchedPapers = computed(() =>
  props.goal ? (papers.value ?? []).filter((p) => p.match).length : 0,
);
const dblpUrl = ref("");
// The paper list: five first, the rest on request; a summary opens on request
const papersShown = ref(5);
const openSummaries = ref(new Set<string>());
function toggleSummary(key: string) {
  const next = new Set(openSummaries.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  openSummaries.value = next;
}
// "ACL (1)" -> "ACL": DBLP numbers a venue's proceedings volumes
function cleanVenue(v: string | null | undefined): string {
  return (v ?? "").replace(/\s*\(\d+\)\s*$/, "").trim();
}
// Abstracts as OpenAlex rebuilds them: "(LRMs).At its core", "AutoRAN 1 , the first"
function cleanAbstract(t: string): string {
  return t
    .replace(/([a-z0-9)\]])\.([A-Z])/g, "$1. $2")
    .replace(/\s+([,.;:)])/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
}
const error = ref("");

watch(
  () => [props.name, props.goal ?? ""] as const,
  async ([name, goal]) => {
    person.value = null;
    papers.value = null;
    papersShown.value = 5;
    openSummaries.value = new Set();
    similar.value = null;
    error.value = "";
    try {
      const profile = await api.profile(name);
      person.value = profile.faculty;
      awards.value = profile.awards;
      collaborators.value = profile.collaborators ?? [];
      previously.value = profile.previously ?? [];
      topics.value = profile.topics ?? [];
    } catch (e) {
      error.value = (e as Error).message;
      return;
    }
    api
      .papers(name, goal)
      .then((r) => {
        papers.value = r.papers;
        dblpUrl.value = r.dblp_url;
      })
      .catch(() => (papers.value = []));
    api
      .similar(name)
      .then((r) => (similar.value = r.similar))
      .catch(() => (similar.value = []));
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
const activeFunderNames = computed(() =>
  [...new Set(activeAwards.value.map((a) => funderName(a.funder)))].join(
    " and ",
  ),
);
const fundedUntil = computed(() => {
  const ends = activeAwards.value.map((a) => a.ends ?? "").sort();
  return ends[ends.length - 1] ?? "";
});

const earlyCareer = computed(
  () =>
    !!person.value?.first_year &&
    person.value.first_year >= new Date().getFullYear() - 6,
);

// A grant held somewhere else than the person's current university (they moved, or it's a partner's).
function heldElsewhere(a: Award): boolean {
  const here = (person.value?.university ?? "").toLowerCase();
  const there = (a.institution ?? "").toLowerCase();
  return (
    !!there &&
    !!here &&
    !there.includes(here) &&
    !here.includes(there.replace(/^the /, ""))
  );
}

function short(name: string) {
  return name.replace(/\s+\d{4}$/, "");
}

// ---- "Before you write": what to read and ask, from what we know about them ----
type Step = { id: string; text: string; link?: string; linkText?: string };
const firstPaper = computed(() => {
  const list = papers.value ?? [];
  return (
    list.find((p) => p.match) ??
    [...list].sort((a, b) => (b.year ?? 0) - (a.year ?? 0))[0] ??
    null
  );
});
const leadGrant = computed(
  () => activeAwards.value.find((a) => a.lead) ?? null,
);
const steps = computed<Step[]>(() => {
  const p = person.value;
  if (!p) return [];
  const out: Step[] = [];
  const paper = firstPaper.value;
  if (paper) {
    out.push({
      id: "read",
      text: `Read ${paper.match ? "the paper closest to your search" : "their newest paper"} (${paper.year ?? "recent"}) and say in a sentence or two what you would build on:`,
      link: webUrl(paper.url) || undefined,
      linkText: paper.title,
    });
  }
  if (props.goal && papers.value) {
    out.push(
      matchedPapers.value
        ? {
            id: "fit",
            text: `${matchedPapers.value} of their recent papers match “${props.goal}”. Name the overlap.`,
          }
        : {
            id: "fit",
            text: `None of their recent papers match “${props.goal}” closely. Explain the connection yourself.`,
          },
    );
  }
  if (leadGrant.value) {
    out.push({
      id: "fund",
      text:
        p.new_lab?.title === leadGrant.value.title
          ? `They lead this ${newLabLabel(p.new_lab.funder, p.new_lab.scheme)} until ${untilLabel(leadGrant.value.ends)}, a grant for PIs starting out. Ask whether it can fund a PhD student:`
          : `They lead an active ${funderName(leadGrant.value.funder)} grant until ${untilLabel(leadGrant.value.ends)}. Ask whether it can fund a PhD student:`,
      link: webUrl(leadGrant.value.url) || undefined,
      linkText: leadGrant.value.title,
    });
  } else if (activeAwards.value.length) {
    out.push({
      id: "fund",
      text: "They're a co-investigator on an active grant. Ask how PhD students in the lab are funded.",
    });
  } else if (fundersFor(p.country).length) {
    out.push({
      id: "fund",
      text: "No active grant on record here. Ask how PhD students in the lab are funded.",
    });
  } else {
    out.push({
      id: "fund",
      text: `There's no grant data for ${countryName(p.country)} here. Ask whether they have a funded PhD position, and look at scholarships for this university.`,
    });
  }
  if (p.new_lab && p.new_lab.title !== leadGrant.value?.title) {
    out.push({
      id: "early",
      text: `Their ${newLabLabel(p.new_lab.funder, p.new_lab.scheme)} is for PIs starting out. Ask whether it funds a student:`,
      link: webUrl(p.new_lab.url) || undefined,
      linkText: p.new_lab.title,
    });
  } else if (earlyCareer.value) {
    out.push({
      id: "early",
      text: "They're early in their career: new labs often recruit their first students, and replies tend to be quicker.",
    });
  }
  if (webUrl(p.homepage)) {
    out.push({
      id: "home",
      text: "Check their homepage for a note to prospective students. Many say how (or whether) to email:",
      link: webUrl(p.homepage) || undefined,
      linkText: "Homepage",
    });
  }
  out.push({
    id: "short",
    text: "Keep the email short: who you are, the paper, your question, CV attached.",
  });
  return out;
});

// Ticks are kept in this browser only.
const ticked = ref<Record<string, boolean>>({});
const tickKey = computed(() => `atlas:before-you-write:${props.name}`);
watch(
  tickKey,
  (k) => {
    try {
      ticked.value = JSON.parse(localStorage.getItem(k) ?? "{}");
    } catch {
      ticked.value = {};
    }
  },
  { immediate: true },
);
function tick(id: string, on: boolean) {
  ticked.value = { ...ticked.value, [id]: on };
  try {
    localStorage.setItem(tickKey.value, JSON.stringify(ticked.value));
  } catch {
    // storage blocked: ticks last for this visit only
  }
}

function untilLabel(date: string | null): string {
  if (!date) return "";
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}
</script>

<template>
  <article class="prof">
    <button type="button" class="back" @click="$emit('back')">
      Back to {{ backLabel }}
    </button>

    <p v-if="error" class="error">{{ error }}</p>
    <LoadingRows v-else-if="!person" label="Loading their profile" :rows="4" />

    <template v-if="person">
      <header>
        <h2>{{ displayName }}</h2>
        <p class="uni">
          <button
            v-if="person.university_id"
            type="button"
            class="uni-link"
            :title="`Open ${person.university} and show it on the map`"
            @click="emit('university', person.university_id)"
          >
            {{ person.university }}
          </button>
          <template v-else>{{ person.university }}</template>
        </p>
        <button
          type="button"
          class="save"
          :class="{ on: isSaved('person', person.name) }"
          :aria-pressed="isSaved('person', person.name)"
          @click="
            toggleSaved({
              kind: 'person',
              id: person.name,
              label: displayName,
              sub: person.university,
              universityId: person.university_id,
            })
          "
        >
          {{
            isSaved("person", person.name)
              ? "Saved to your list"
              : "Save to your list"
          }}
        </button>
        <p v-if="previously.length" class="prev">
          Previously at {{ previously.join(", ") }}
        </p>
        <p v-if="person.new_lab" class="early">
          New lab, funded:
          {{ newLabLabel(person.new_lab.funder, person.new_lab.scheme) }},
          running until {{ untilLabel(person.new_lab.ends) }}. PIs starting out
          with money like this are usually recruiting their first students.
        </p>
        <p v-else-if="earlyCareer" class="early">
          Early career: first top-venue paper in {{ person.first_year }}. Newer
          faculty are often building a lab and looking for students.
        </p>
        <p class="links">
          <a
            v-if="webUrl(person.homepage)"
            :href="webUrl(person.homepage)"
            target="_blank"
            rel="noopener"
            >Homepage</a
          >
          <a
            v-if="person.scholar_id"
            :href="`https://scholar.google.com/citations?user=${encodeURIComponent(person.scholar_id)}`"
            target="_blank"
            rel="noopener"
            >Google Scholar</a
          >
          <a
            v-if="dblpUrl && person.source !== 'openalex'"
            :href="dblpUrl"
            target="_blank"
            rel="noopener"
            >DBLP</a
          >
          <a
            v-if="person.orcid"
            :href="`https://orcid.org/${person.orcid}`"
            target="_blank"
            rel="noopener"
            >ORCID</a
          >
          <a
            v-if="person.openalex_id"
            :href="`https://openalex.org/${person.openalex_id}`"
            target="_blank"
            rel="noopener"
            >OpenAlex</a
          >
        </p>
      </header>

      <section
        v-if="person.source !== 'openalex' || papers?.length"
        class="before"
      >
        <h3>Before you write</h3>
        <ul class="steps">
          <li v-for="st in steps" :key="st.id">
            <label>
              <input
                type="checkbox"
                :checked="!!ticked[st.id]"
                @change="
                  tick(st.id, ($event.target as HTMLInputElement).checked)
                "
              />
              <span>
                {{ st.text }}
                <a
                  v-if="st.link"
                  :href="st.link"
                  target="_blank"
                  rel="noopener"
                  >{{ st.linkText }}</a
                ><template v-else-if="st.linkText">
                  “{{ st.linkText }}”</template
                >
              </span>
            </label>
          </li>
        </ul>
      </section>

      <section>
        <h3>Research areas</h3>
        <p v-if="person.source === 'openalex'" class="hint">
          Their main research areas, from OpenAlex. Listed as a researcher at
          this university by OpenAlex; check their department page to confirm
          they supervise PhD students.
        </p>
        <p v-else class="hint">
          Papers at top venues in the last 10 years, from CSRankings
        </p>
        <ul class="areas">
          <li v-for="a in areaList" :key="a.area" :style="{ '--c': a.color }">
            <span class="area-name">{{ a.name }}</span>
            <!-- OpenAlex researchers' papers aren't split by area: every area got the full count -->
            <span v-if="person.source !== 'openalex'" class="num"
              >{{ a.pubs }} {{ a.pubs === 1 ? "paper" : "papers" }}</span
            >
          </li>
        </ul>
      </section>

      <section v-if="topics.length">
        <h3>Working on now</h3>
        <p class="hint">Topics of their recent papers, from OpenAlex</p>
        <ul class="topics">
          <li v-for="t in topics" :key="t.topic">
            {{ t.topic }} <span class="num">{{ t.papers }}</span>
          </li>
        </ul>
      </section>

      <section>
        <h3>Funding</h3>
        <p
          v-if="!fundersFor(person.country).length && !awards.length"
          class="funding-note"
        >
          Grant data for {{ countryName(person.country) }} isn't in Advisor
          Atlas yet, so this professor's funding isn't shown. Ask them about
          funded PhD positions.
        </p>
        <p v-else-if="activeAwards.length" class="funding-note">
          <span class="fund-dot on" aria-hidden="true"></span>
          {{ activeAwards.length }} active {{ activeFunderNames }}
          {{ activeAwards.length === 1 ? "grant" : "grants" }}, running until
          {{ untilLabel(fundedUntil) }}. Grants like these usually pay PhD
          students as research assistants, so it's worth asking about openings
          when you write.
        </p>
        <p v-else class="funding-note">
          <span class="fund-dot" aria-hidden="true"></span>
          No active
          {{
            fundersFor(person.country).map(funderName).join(" or ") ||
            "research"
          }}
          grant on record. They may be funded by industry or other agencies,
          which this data doesn't cover, so ask.
        </p>
      </section>

      <section>
        <h3>
          {{
            matchedPapers ? "Papers closest to your search" : "Recent papers"
          }}
        </h3>
        <p v-if="matchedPapers" class="hint">
          {{ matchedPapers }} of their recent papers match “{{ goal }}”; the
          rest follow, newest first.
        </p>
        <LoadingRows v-if="papers === null" label="Loading papers" :rows="3" />
        <p v-else-if="!papers.length" class="hint">
          No recent papers loaded for this professor yet.
        </p>
        <ol v-else class="papers">
          <li
            v-for="p in papers.slice(0, papersShown)"
            :key="p.title"
            :class="{ matched: p.match }"
          >
            <a
              v-if="webUrl(p.url)"
              :href="webUrl(p.url)"
              target="_blank"
              rel="noopener"
              class="ptitle"
              >{{ p.title }}</a
            >
            <span v-else class="ptitle">{{ p.title }}</span>
            <span class="meta">
              {{ [cleanVenue(p.venue), p.year].filter(Boolean).join(" ")
              }}{{
                p.cited_by
                  ? `, cited ${p.cited_by} ${p.cited_by === 1 ? "time" : "times"}`
                  : ""
              }}
            </span>
            <template v-if="p.snippet">
              <p class="snippet" :class="{ open: openSummaries.has(p.title) }">
                {{ cleanAbstract(p.snippet) }}
              </p>
              <button
                v-if="p.snippet.length > 160"
                type="button"
                class="link toggle-summary"
                :aria-expanded="openSummaries.has(p.title)"
                @click="toggleSummary(p.title)"
              >
                {{ openSummaries.has(p.title) ? "Less" : "More" }}
              </button>
            </template>
          </li>
        </ol>
        <button
          v-if="papers && papers.length > papersShown"
          type="button"
          class="show-more"
          @click="papersShown += 10"
        >
          Show more papers ({{ papers.length - papersShown }} left)
        </button>
      </section>

      <section>
        <h3>Research grants</h3>
        <p v-if="!awards.length" class="hint">
          No grants linked to this professor in the funders Advisor Atlas
          covers.
        </p>
        <ol class="awards">
          <li v-for="a in awards" :key="a.id" :class="{ active: a.active }">
            <button
              type="button"
              class="link award-title"
              title="Read the grant: what it funds, who is on it"
              @click="showGrant(a.funder, a.id)"
            >
              {{ grantTitle(a.title) }}
            </button>
            <p class="meta">
              {{ funderName(a.funder) }},
              <span class="num">{{ formatMoney(a.amount, a.currency) }}</span
              >, {{ formatYear(a.starts) }}&ndash;{{ formatYear(a.ends) }},
              {{ a.lead ? "lead" : "co-investigator"
              }}<strong v-if="a.active">, active</strong>
            </p>
            <p v-if="heldElsewhere(a)" class="meta">
              Held at {{ a.institution }}
            </p>
            <p v-if="a.team?.length" class="meta team">
              With
              <template v-for="(m, i) in a.team.slice(0, 6)" :key="m.name">
                <button
                  v-if="m.profile"
                  type="button"
                  class="link"
                  @click="emit('open', m.profile)"
                >
                  {{ short(m.name) }}</button
                ><span v-else>{{ m.name }}</span
                ><template v-if="i < Math.min(a.team.length, 6) - 1"
                  >,
                </template>
              </template>
              <template v-if="a.team.length > 6">
                and {{ a.team.length - 6 }} more</template
              >
            </p>
            <details v-if="a.abstract">
              <summary>Abstract</summary>
              <p>{{ a.abstract }}&hellip;</p>
            </details>
          </li>
        </ol>
      </section>

      <section v-if="collaborators.length">
        <h3>Works with</h3>
        <p class="hint">
          People in Advisor Atlas they've published with recently
        </p>
        <ul class="people">
          <li v-for="c in collaborators" :key="c.name">
            <button type="button" class="link" @click="emit('open', c.name)">
              {{ short(c.name) }}
            </button>
            <span class="meta"
              >{{ c.university }}, {{ c.papers }} shared
              {{ c.papers === 1 ? "paper" : "papers" }}</span
            >
          </li>
        </ul>
      </section>

      <section v-if="similar === null || similar.length">
        <h3>Researchers with similar work</h3>
        <LoadingRows
          v-if="similar === null"
          label="Finding similar researchers"
          :rows="2"
        />
        <ul v-else class="people">
          <li v-for="p in similar" :key="p.name">
            <button type="button" class="link" @click="emit('open', p.name)">
              {{ short(p.name) }}
            </button>
            <span class="meta">{{ p.university }}</span>
          </li>
        </ul>
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

.save {
  margin-top: 8px;
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: #fff;
  padding: 3px 12px 2px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink);
  cursor: pointer;
}

.save.on {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
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
.uni-link {
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: left;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
  cursor: pointer;
}
.uni-link:hover {
  color: var(--ink);
  text-decoration-color: currentColor;
}

.prev,
.early {
  margin-top: 4px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.early {
  color: var(--line-systems);
  font-weight: 600;
}

.before {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--radius-box);
  padding: 12px 14px 14px;
}

.before h3 {
  border-bottom: 0;
  padding-bottom: 0;
}

.steps {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.steps label {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: start;
  font-size: var(--t-sm);
  line-height: 1.45;
}

.steps input {
  margin-top: 3px;
}

.steps input:checked + span {
  color: var(--ink-faint);
}

.steps a {
  font-weight: 600;
}

.topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
}

.topics li {
  font-size: var(--t-xs);
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  padding: 3px 10px 2px;
}

.topics .num {
  color: var(--ink-faint);
  margin-left: 4px;
}

.snippet {
  margin-top: 4px;
  font-size: var(--t-xs);
  line-height: 1.45;
  color: var(--ink-soft);
  /* two lines until opened */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
.snippet.open {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset;
}
.toggle-summary {
  margin-top: 2px;
  font-size: var(--t-xs);
  font-weight: 600;
  color: var(--ink-soft);
}

.team {
  line-height: 1.5;
}

.people {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 6px;
}

.people li {
  display: grid;
  gap: 1px;
}

.link {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  font-weight: 700;
  color: var(--ink);
  text-align: left;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
  cursor: pointer;
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

.papers li.matched {
  border-left: 3px solid var(--line-ai);
  padding-left: 10px;
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
/* a paper's title opens the paper: underlined faintly, so it reads as a link */
.papers a.ptitle {
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
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
