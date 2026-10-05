<script setup lang="ts">
import { LINE_COLOR, webUrl } from "@/lines";
import { computed, ref, watch } from "vue";
import {
  api,
  type Faculty,
  type Query,
  type Scholarship,
  type UniversityDetail,
} from "@/api";
import { countryName } from "@/countries";
import { isSaved, toggleSaved } from "@/shortlist";
import { areaIndex, funderName } from "@/store";
import FacultyRow from "./FacultyRow.vue";
import ProfessorView from "./ProfessorView.vue";

const props = defineProps<{
  id: string;
  query: Query;
  professor: string | null;
}>();
const emit = defineEmits<{ close: []; openProfessor: [name: string | null] }>();

const uni = ref<UniversityDetail | null>(null);
const faculty = ref<Faculty[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [detail, people] = await Promise.all([
      api.university(props.id),
      api.faculty({ ...props.query, university: props.id, limit: 150 }),
    ]);
    uni.value = detail;
    faculty.value = people;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

watch(() => [props.id, props.query.areas.join(","), props.query.goal], load, {
  immediate: true,
});

// Scholarships for studying in this university's country; students check eligibility on each programme's page.
const scholarships = ref<Scholarship[]>([]);
// A level to narrow by (only the levels present are offered).
const schLevel = ref("");
const schLevels = computed(() =>
  ["masters", "phd", "postdoc"].filter((l) =>
    scholarships.value.some((s) => s.levels.includes(l)),
  ),
);
const atLevel = (s: Scholarship) =>
  !schLevel.value || s.levels.includes(schLevel.value);

// Application windows are free text ("approx. Jun–Aug"); read the first month range when there is one.
const MONTHS = [
  "jan",
  "feb",
  "mar",
  "apr",
  "may",
  "jun",
  "jul",
  "aug",
  "sep",
  "oct",
  "nov",
  "dec",
];
const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];
type Window = { open: boolean; label: string; order: number };
function windowOf(text: string): Window | null {
  const m =
    /\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*[–-]\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i.exec(
      text,
    );
  if (!m) return null;
  const from = MONTHS.indexOf(m[1].toLowerCase());
  const to = MONTHS.indexOf(m[2].toLowerCase());
  const now = new Date().getMonth();
  const open = from <= to ? now >= from && now <= to : now >= from || now <= to;
  if (open)
    return {
      open,
      label: `Open now, until about ${MONTH_NAMES[to]}`,
      order: 0,
    };
  const wait = (from - now + 12) % 12;
  return { open, label: `Opens about ${MONTH_NAMES[from]}`, order: wait };
}
const byWindow = (a: Scholarship, b: Scholarship) =>
  (windowOf(a.application_window)?.order ?? 99) -
  (windowOf(b.application_window)?.order ?? 99);

const curatedScholarships = computed(() =>
  scholarships.value
    .filter((s) => s.source !== "daad" && atLevel(s))
    .sort(byWindow),
);
const feedScholarships = computed(() =>
  scholarships.value.filter((s) => s.source === "daad" && atLevel(s)),
);
watch(
  () => uni.value?.country,
  async () => {
    if (!uni.value?.country) return;
    try {
      scholarships.value = await api.scholarships(uni.value.country);
    } catch {
      scholarships.value = [];
    }
  },
);
const isUS = computed(() => uni.value?.country === "us");
const allTraining = ref(false);
// With a search, programmes whose titles share a word with it come first.
const shownTraining = computed(() => {
  const words = (props.query.goal ?? "")
    .toLowerCase()
    .split(/\W+/)
    .filter((w) => w.length > 3);
  const hits = (t: string) =>
    words.filter((w) => t.toLowerCase().includes(w)).length;
  const list = [...(uni.value?.training ?? [])].sort(
    (a, b) => hits(b.title) - hits(a.title),
  );
  return allTraining.value ? list : list.slice(0, 4);
});
// Funders whose grants are loaded for this university's country (NSF for the US, ARC for Australia, ...).
const grantFunders = computed(
  () => uni.value?.grant_funders ?? (isUS.value ? ["nsf"] : []),
);
// Named in "have an active … grant": the funders this university's faculty actually hold grants from.
const grantFunderNames = computed(() => {
  const held = (uni.value?.funders ?? [])
    .filter((f) => f.people > 0)
    .map((f) => f.funder);
  const names = (held.length ? held : grantFunders.value).map(funderName);
  return names.length > 1
    ? `${names.slice(0, -1).join(", ")} or ${names[names.length - 1]}`
    : (names[0] ?? "");
});
const ercOnly = computed(
  () => grantFunders.value.length === 1 && grantFunders.value[0] === "erc",
);
const countryLabel = computed(() => countryName(uni.value?.country));
function levelLabel(levels: string[]) {
  const names: Record<string, string> = {
    masters: "Master's",
    phd: "PhD",
    postdoc: "Postdoc",
  };
  return levels
    .map((l) => names[l] ?? l)
    .filter(Boolean)
    .join(", ");
}

const hasAreas = computed(() => props.query.areas.length > 0);
const funded = computed(
  () =>
    faculty.value.filter(
      (f) => f.active_awards > 0 || f.funding?.some((x) => x.active > 0),
    ).length,
);
const place = computed(() =>
  [uni.value?.city, uni.value?.state].filter(Boolean).join(", "),
);
const carnegieLabel = computed(() =>
  uni.value?.carnegie === "R1"
    ? "R1: very high research activity"
    : uni.value?.carnegie === "R2"
      ? "R2: high research activity"
      : "",
);

// The university's strongest areas by faculty count (from the explorer), with their line colours.
// Computer science areas only: researchers in other fields come from OpenAlex capped at 20 per
// field and university, so their counts would read as equal strengths everywhere.
const OPENALEX_GROUPS = new Set(["Sciences", "Engineering", "Medicine", "Social sciences & humanities"]);
const strengths = computed(() => {
  const entries = Object.entries(uni.value?.area_faculty ?? {})
    .filter(([area]) => !OPENALEX_GROUPS.has(areaIndex.value.get(area)?.group ?? ""))
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  const top = entries[0]?.[1] ?? 1;
  return entries.map(([area, n]) => {
    const info = areaIndex.value.get(area);
    return {
      area,
      n,
      name: info?.name ?? area,
      width: (100 * n) / top,
      color: LINE_COLOR[info?.group ?? ""] ?? "var(--ink-soft)",
    };
  });
});

// Curated entries sometimes say "see official page"; that adds nothing on a card that links there.
function shown(v: string | undefined) {
  return !!v && !/^see (the )?(official|programme) page/i.test(v.trim());
}

function money(n?: number) {
  return n ? `$${n.toLocaleString("en-US")}` : "";
}
</script>

<template>
  <aside class="drawer" :aria-label="uni?.name ?? 'University'">
    <button
      type="button"
      class="close"
      aria-label="Close"
      @click="emit('close')"
    >
      Close
    </button>

    <ProfessorView
      v-if="professor"
      :name="professor"
      :back-label="uni?.name ?? 'university'"
      :goal="query.goal"
      @back="emit('openProfessor', null)"
      @open="(n: string) => emit('openProfessor', n)"
    />

    <div v-else class="uni">
      <p v-if="error" class="error">{{ error }}</p>
      <template v-if="uni">
        <header>
          <h2>{{ uni.name }}</h2>
          <p class="place">{{ place }}</p>
          <p v-if="carnegieLabel" class="carnegie">{{ carnegieLabel }}</p>
          <button
            type="button"
            class="save"
            :class="{ on: isSaved('university', uni.id) }"
            :aria-pressed="isSaved('university', uni.id)"
            @click="
              toggleSaved({
                kind: 'university',
                id: uni.id,
                label: uni.name,
                sub: place,
              })
            "
          >
            {{
              isSaved("university", uni.id)
                ? "Saved to your list"
                : "Save to your list"
            }}
          </button>
        </header>

        <dl class="facts">
          <div>
            <dt>Faculty and researchers listed</dt>
            <dd class="num">{{ uni.faculty_total }}</dd>
          </div>
          <div v-if="uni.grad_enrollment">
            <dt>Graduate students</dt>
            <dd class="num">
              {{ uni.grad_enrollment.toLocaleString("en-US") }}
            </dd>
          </div>
          <div v-if="uni.doctoral_degrees">
            <dt>PhDs awarded, all fields ({{ uni.doctoral_year }})</dt>
            <dd class="num">
              {{ uni.doctoral_degrees.toLocaleString("en-US") }}
            </dd>
          </div>
          <div v-if="uni.grad_tuition_out_of_state">
            <dt>Graduate tuition per year</dt>
            <dd class="num">
              {{ money(uni.grad_tuition_out_of_state) }}
              <span
                v-if="
                  uni.grad_tuition_in_state &&
                  uni.grad_tuition_in_state !== uni.grad_tuition_out_of_state
                "
                class="sub"
              >
                {{ money(uni.grad_tuition_in_state) }} in-state
              </span>
            </dd>
          </div>
        </dl>

        <section v-if="strengths.length" class="strengths">
          <h3>Research strengths</h3>
          <p class="sub">Faculty and researchers listed here, by area</p>
          <ul>
            <li v-for="a in strengths" :key="a.area">
              <span class="s-name">{{ a.name }}</span>
              <span class="s-track"
                ><span
                  class="s-fill"
                  :style="{ width: a.width + '%', background: a.color }"
                ></span
              ></span>
              <span class="num">{{ a.n }}</span>
            </li>
          </ul>
        </section>

        <section class="funding">
          <h3>Paying for a PhD here</h3>
          <template v-if="grantFunders.length">
            <p>
              <strong class="num">{{ funded }}</strong> of the
              {{ faculty.length }}
              {{
                query.goal
                  ? "faculty matching your search"
                  : hasAreas
                    ? "faculty in your areas"
                    : "faculty listed below"
              }}
              have an active {{ grantFunderNames }} grant. PhD students are
              usually paid as research or teaching assistants, which also covers
              tuition, and faculty with active grants are the ones hiring
              research assistants.
            </p>
            <ul v-if="uni.funders?.length" class="funders">
              <li v-for="fd in uni.funders" :key="fd.funder">
                <strong>{{ funderName(fd.funder) }}</strong
                >: {{ fd.people }}
                {{ fd.people === 1 ? "person" : "people" }} with grants on
                record, {{ fd.active_people }} with one running now
              </li>
            </ul>
            <div v-if="uni.recently_funded?.length" class="recent">
              <p class="sub">Recently funded (likely hiring):</p>
              <ul>
                <li v-for="g in uni.recently_funded" :key="g.name + g.title">
                  <button
                    type="button"
                    class="link"
                    @click="emit('openProfessor', g.name)"
                  >
                    {{ g.name.replace(/\s+\d{4}$/, "") }}</button
                  >, {{ funderName(g.funder) }} {{ g.year }}: {{ g.title }}
                </li>
              </ul>
            </div>
            <p v-if="ercOnly" class="sub">
              ERC grants are rare, highly competitive awards, and most PhD
              positions in {{ countryLabel }} are paid from national agencies
              and university budgets that aren't in Advisor Atlas yet. Read "no
              ERC grant" as "no data", not "no funding".
            </p>
          </template>
          <p v-else>
            Grant data for universities in {{ countryLabel }} isn't in Advisor
            Atlas yet, so faculty funding isn't shown. Ask faculty directly
            about funded PhD positions, and see the scholarships below.
          </p>
          <div v-if="uni.training?.length" class="recent training">
            <p class="sub">
              Funded PhD programmes ({{ uni.training.length }}): training grants
              that pay students' stipends and tuition. Apply to the programme,
              not to one professor.
            </p>
            <ul>
              <li v-for="g in shownTraining" :key="g.title">
                <a
                  v-if="webUrl(g.url)"
                  :href="webUrl(g.url)"
                  target="_blank"
                  rel="noopener"
                  >{{ g.title }}</a
                >
                <span v-else>{{ g.title }}</span
                >, {{ funderName(g.funder) }}, until
                {{ (g.ends ?? "").slice(0, 4)
                }}<template v-if="g.lead"
                  >, led by
                  <button
                    v-if="g.profile"
                    type="button"
                    class="link"
                    @click="emit('openProfessor', g.profile)"
                  >
                    {{ g.profile.replace(/\s+\d{4}$/, "") }}</button
                  ><template v-else>{{ g.lead }}</template></template
                >
              </li>
            </ul>
            <button
              v-if="uni.training.length > 4"
              type="button"
              class="link more"
              @click="allTraining = !allTraining"
            >
              {{ allTraining ? "Fewer" : `All ${uni.training.length}` }}
            </button>
          </div>
        </section>

        <section class="scholarships">
          <h3>Funding you can apply for</h3>
          <p v-if="!scholarships.length" class="sub">
            No scholarships in our list for study in {{ countryLabel }}.
          </p>
          <p
            v-if="schLevels.length > 1"
            class="levels"
            role="group"
            aria-label="Level"
          >
            <button
              type="button"
              :class="{ on: !schLevel }"
              @click="schLevel = ''"
            >
              All
            </button>
            <button
              v-for="l in schLevels"
              :key="l"
              type="button"
              :class="{ on: schLevel === l }"
              @click="schLevel = l"
            >
              {{ levelLabel([l]) }}
            </button>
          </p>
          <ul class="sch-list">
            <li v-for="sch in curatedScholarships" :key="sch.id">
              <a
                :href="webUrl(sch.url)"
                target="_blank"
                rel="noopener"
                class="sch-name"
                >{{ sch.name }}</a
              >
              <p
                v-if="windowOf(sch.application_window)"
                class="window"
                :class="{ open: windowOf(sch.application_window)?.open }"
              >
                {{ windowOf(sch.application_window)?.label }}
              </p>
              <p class="sub">
                {{ sch.provider }}. {{ levelLabel(sch.levels) }}.
                <template v-if="shown(sch.covers)"
                  >Covers {{ sch.covers }}.{{ " " }}</template
                >
                <template v-if="shown(sch.application_window)"
                  >Application window: {{ sch.application_window }}.</template
                >
              </p>
              <p v-if="sch.notes" class="sub">{{ sch.notes }}</p>
              <p class="elig">Check eligibility on the official page</p>
            </li>
          </ul>
          <details v-if="feedScholarships.length" class="sch-more">
            <summary>
              More from the DAAD scholarship database ({{
                feedScholarships.length
              }})
            </summary>
            <ul class="sch-list">
              <li v-for="sch in feedScholarships" :key="sch.id">
                <a
                  :href="webUrl(sch.url)"
                  target="_blank"
                  rel="noopener"
                  class="sch-name"
                  >{{ sch.name }}</a
                >
                <p class="sub">
                  {{ sch.provider }}. {{ levelLabel(sch.levels) }}.
                  <template v-if="sch.application_window">{{
                    sch.application_window
                  }}</template>
                </p>
                <p v-if="sch.notes" class="sub">{{ sch.notes }}</p>
              </li>
            </ul>
          </details>
          <p class="sub">
            Rules and deadlines change every year: always confirm on the
            official page.
          </p>
        </section>

        <section>
          <h3>
            {{
              query.goal
                ? "Faculty whose work matches your goal"
                : hasAreas
                  ? "Faculty in your areas"
                  : "Faculty"
            }}
          </h3>
          <p v-if="!loading && !faculty.length" class="sub">
            No faculty here match. Try fewer words in your goal, or another
            area.
          </p>
          <ul class="list">
            <FacultyRow
              v-for="f in faculty"
              :key="f.name"
              :person="f"
              :selected-areas="query.areas"
              @open="emit('openProfessor', $event)"
            />
          </ul>
        </section>

        <a
          v-if="webUrl(uni.homepage)"
          class="home"
          :href="webUrl(uni.homepage)"
          target="_blank"
          rel="noopener"
        >
          University website
        </a>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.drawer {
  position: relative;
  height: 100%;
  overflow-y: auto;
  background: var(--surface);
  border-left: 1px solid var(--rule);
  padding: 22px 24px 40px;
}

.close {
  position: absolute;
  top: 18px;
  right: 18px;
  border: 1.5px solid var(--rule-strong);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 3px 12px 2px;
  font-size: var(--t-xs);
  font-weight: 700;
}

.uni {
  display: grid;
  gap: 22px;
}

h2 {
  font-size: var(--t-xl);
  font-weight: 800;
  letter-spacing: -0.01em;
  padding-right: 70px;
}

.place {
  margin-top: 4px;
  color: var(--ink-soft);
}

.carnegie {
  display: inline-block;
  margin-top: 10px;
  padding: 3px 10px 2px;
  border: 2.5px solid var(--ink);
  border-radius: var(--radius-pill);
  font-size: var(--t-xs);
  font-weight: 800;
}

.facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 14px;
  margin: 0;
}

.facts dt {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.facts dd {
  margin: 2px 0 0;
  font-size: var(--t-lg);
  font-weight: 800;
}

.sub {
  display: block;
  font-size: var(--t-xs);
  font-weight: 400;
  color: var(--ink-soft);
}

h3 {
  font-size: var(--t-sm);
  font-weight: 800;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 8px;
}

.funding p + p {
  margin-top: 8px;
}

.sch-list {
  margin: 0;
  padding: 0;
}

.sch-list li {
  list-style: none;
  padding: 9px 0;
  border-bottom: 1px solid var(--rule);
}

.sch-name {
  font-weight: 700;
}

.strengths ul,
.funders,
.recent ul {
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
}

.strengths li {
  display: grid;
  grid-template-columns: minmax(0, 11rem) 1fr 2.5rem;
  align-items: center;
  gap: 10px;
  padding: 3px 0;
  font-size: var(--t-xs);
}

.s-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.s-track {
  height: 8px;
  background: var(--rule);
  border-radius: 2px;
  position: relative;
}

.s-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 2px;
}

.strengths .num {
  text-align: right;
}

.funders li,
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

.training {
  margin-top: 14px;
}

.recent .more {
  margin-top: 4px;
  font-size: var(--t-xs);
}

.levels {
  display: flex;
  gap: 6px;
  margin: 4px 0 10px;
}

.levels button {
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: #fff;
  padding: 3px 10px 2px;
  font: inherit;
  font-size: var(--t-xs);
  color: var(--ink);
  cursor: pointer;
}

.levels button.on {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
}

.window {
  margin: 2px 0;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink-soft);
}

.window.open {
  color: var(--line-systems);
}

.recent li {
  font-size: var(--t-xs);
  padding: 3px 0;
  line-height: 1.45;
}

.recent .link {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  font-weight: 700;
  color: var(--ink);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.sch-more {
  margin-top: 10px;
}

.sch-more summary {
  cursor: pointer;
  font-weight: 700;
  font-size: var(--t-sm);
  padding: 6px 0;
}

.elig {
  margin-top: 4px;
  font-size: var(--t-xs);
  font-weight: 700;
}

.list {
  margin: 0;
  padding: 0;
}

.home {
  font-weight: 700;
  font-size: var(--t-xs);
}

.error {
  color: var(--danger);
}
</style>
