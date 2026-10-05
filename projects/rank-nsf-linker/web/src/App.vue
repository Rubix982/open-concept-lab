<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  api,
  type Faculty,
  type Grant,
  type Query,
  type UniversitySummary,
} from "@/api";
import { INK_HEX, LINE_COLOR, LINE_HEX } from "@/lines";
import { areaIndex, areas, funderName, funders, fundersFor } from "@/store";
import { countryName } from "@/countries";
import AreaPicker from "@/components/AreaPicker.vue";
import FacultyRow from "@/components/FacultyRow.vue";
import FundingView from "@/components/FundingView.vue";
import ShortlistDialog from "@/components/ShortlistDialog.vue";
import { saved } from "@/shortlist";
import MapView from "@/components/MapView.vue";
import UniversityDrawer from "@/components/UniversityDrawer.vue";

// ---- state, mirrored in the URL so a search can be shared ----
const url = new URLSearchParams(location.search);
const selectedAreas = ref<string[]>(
  url.get("areas")?.split(",").filter(Boolean) ?? [],
);
const goalInput = ref(url.get("q") ?? "");
const goal = ref(goalInput.value);
// "Grants" was folded into "Funding"; old links with view=grants open Funding.
type Tab = "universities" | "faculty" | "funding";
const tab = ref<Tab>(
  (["faculty", "grants", "funding"].includes(url.get("view") ?? "")
    ? url.get("view")?.replace("grants", "funding")
    : "universities") as Tab,
);
const openUni = ref<string | null>(url.get("u"));
const openProf = ref<string | null>(url.get("p"));
// Narrowing filters, also in the URL.
const country = ref(url.get("country") ?? "");
const onlyFunded = ref(url.get("funded") === "1");
const onlyEarly = ref(url.get("early") === "1");
const onlyR1 = ref(url.get("r1") === "1");
const onlyNewLab = ref(url.get("newlab") === "1");
type Sort = "" | "recent" | "funding";
const sortBy = ref<Sort>(
  (["recent", "funding"].includes(url.get("sort") ?? "")
    ? url.get("sort")
    : "") as Sort,
);
const filterParams = computed(() => ({
  country: country.value || undefined,
  funded: onlyFunded.value ? 1 : undefined,
  early: onlyEarly.value ? 1 : undefined,
  r1: onlyR1.value ? 1 : undefined,
  newlab: onlyNewLab.value ? 1 : undefined,
  sort: sortBy.value || undefined,
}));
// One line about a chosen country: what's listed, which grants we have, scholarships.
const countryScholarships = ref<number | null>(null);
watch(
  country,
  async (c) => {
    countryScholarships.value = null;
    if (!c) return;
    try {
      countryScholarships.value = (await api.scholarships(c)).length;
    } catch {
      countryScholarships.value = null;
    }
  },
  { immediate: true },
);
const countryNote = computed(() => {
  if (!country.value) return "";
  const f = fundersFor(country.value).map(funderName);
  const grants = f.length
    ? `Grant data from ${f.join(", ")}.`
    : "No grant data for this country yet.";
  const sch =
    countryScholarships.value === null
      ? ""
      : ` ${countryScholarships.value} ${countryScholarships.value === 1 ? "scholarship" : "scholarships"} listed for study here (open a university to see them).`;
  return `${countryName(country.value)}: ${grants}${sch}`;
});
const filtersOn = computed(
  () =>
    !!(
      country.value ||
      onlyFunded.value ||
      onlyEarly.value ||
      onlyR1.value ||
      onlyNewLab.value
    ),
);
function clearFilters() {
  country.value = "";
  onlyFunded.value = onlyEarly.value = onlyR1.value = onlyNewLab.value = false;
}

const query = computed<Query>(() => ({
  areas: selectedAreas.value,
  goal: goal.value,
}));

watch(
  [selectedAreas, goal, tab, openUni, openProf, filterParams],
  () => {
    const p = new URLSearchParams();
    if (selectedAreas.value.length)
      p.set("areas", selectedAreas.value.join(","));
    if (goal.value) p.set("q", goal.value);
    if (tab.value !== "universities") p.set("view", tab.value);
    if (openUni.value) p.set("u", openUni.value);
    if (openProf.value) p.set("p", openProf.value);
    for (const [k, v] of Object.entries(filterParams.value))
      if (v !== undefined) p.set(k, String(v));
    const s = p.toString();
    history.replaceState(null, "", s ? `?${s}` : location.pathname);
  },
  { immediate: true },
); // immediate: an old ?view=grants link is rewritten to view=funding

// The goal box searches when submitted (Enter or the Search button), not while typing.
function submitGoal() {
  const g = goalInput.value.trim();
  if (!g) return clearGoal();
  goal.value = g;
  openUniversity(null);
  if (tab.value === "universities") tab.value = "faculty";
}

// Starting points for someone who doesn't know the words yet, across fields.
const EXAMPLES = [
  "mechanistic interpretability",
  "robot learning",
  "low-resource languages",
  "climate modelling",
  "protein design",
  "quantum error correction",
  "malaria vaccine",
];
function trySearch(q: string) {
  goalInput.value = q;
  submitGoal();
}

function clearGoal() {
  goalInput.value = "";
  goal.value = "";
  if (tab.value === "funding") tab.value = "faculty";
}

// ---- data ----
const universities = ref<UniversitySummary[]>([]);
const faculty = ref<Faculty[]>([]);
const grants = ref<Grant[]>([]);
const grantsLoading = ref(false);
const includePastGrants = ref(true); // the Funding tab opens on every grant; a toggle narrows to running
const loading = ref(true);
const error = ref("");
// The map renders only once the area list and the first university load have both arrived.
const ready = ref(false);
let inflight: AbortController | null = null;

async function load() {
  inflight?.abort();
  inflight = new AbortController();
  loading.value = true;
  error.value = "";
  try {
    const [u, f] = await Promise.all([
      api.universities(query.value, inflight.signal),
      api.faculty(
        { ...query.value, ...filterParams.value, limit: 60 },
        inflight.signal,
      ),
    ]);
    universities.value = u;
    faculty.value = f;
    loading.value = false;
    if (areas.value.length) ready.value = true;
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
    error.value = (e as Error).message;
    loading.value = false;
  }
}

async function loadAreas() {
  api
    .funders()
    .then((f) => (funders.value = f))
    .catch(() => {});
  try {
    areas.value = await api.areas();
    if (!loading.value && !error.value) ready.value = true;
  } catch (e) {
    error.value = (e as Error).message;
  }
}

function retry() {
  error.value = "";
  if (!areas.value.length) loadAreas();
  load();
}

let grantsInflight: AbortController | null = null;
async function loadGrants() {
  grantsInflight?.abort();
  if (!goal.value) {
    grants.value = [];
    return;
  }
  grantsInflight = new AbortController();
  grantsLoading.value = true;
  try {
    grants.value = await api.grants(
      { ...query.value, active: !includePastGrants.value, limit: 40 },
      grantsInflight.signal,
    );
  } catch (e) {
    if ((e as Error).name !== "AbortError") error.value = (e as Error).message;
  } finally {
    grantsLoading.value = false;
  }
}

onMounted(loadAreas);
watch([query, filterParams], load, { immediate: true, deep: true });
watch([query, includePastGrants], loadGrants, { immediate: true, deep: true });

// ---- derived ----
const selectedNames = computed(() =>
  selectedAreas.value.map((a) => areaIndex.value.get(a)?.name ?? a),
);

// Dots take the line colour when every chosen area is on one line.
const mapColor = computed(() => {
  const groups = new Set(
    selectedAreas.value.map((a) => areaIndex.value.get(a)?.group),
  );
  return groups.size === 1
    ? (LINE_HEX[[...groups][0] ?? ""] ?? INK_HEX)
    : INK_HEX;
});

// On the Funding tab the dots show money (grants on the search) instead of people.
const fundingCounts = ref<Record<string, number> | null>(null);
const fundingMap = computed(
  () => tab.value === "funding" && !!goal.value && !!fundingCounts.value,
);
const mapUniversities = computed(() =>
  fundingMap.value
    ? shownUniversities.value.map((u) => ({
        ...u,
        goal_matches: fundingCounts.value?.[u.id] ?? 0,
      }))
    : shownUniversities.value,
);

// Countries with listed universities, most universities first, for the country filter.
const countryOptions = computed(() => {
  const n = new Map<string, number>();
  for (const u of universities.value)
    if (u.country && u.faculty > 0)
      n.set(u.country, (n.get(u.country) ?? 0) + 1);
  return [...n.entries()]
    .map(([code, count]) => ({ code, count, name: countryName(code) }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

// The university filters (the faculty filters run on the server). Early career has no university meaning.
const shownUniversities = computed(() =>
  universities.value.filter(
    (u) =>
      (!country.value || u.country === country.value) &&
      (!onlyR1.value || u.carnegie === "R1") &&
      (!onlyFunded.value || u.funded > 0),
  ),
);

const rankedUniversities = computed(() =>
  shownUniversities.value
    .filter((u) => (goal.value ? u.goal_matches > 0 : u.faculty > 0))
    .slice(0, 80),
);

// Universities with matching faculty: the map fits to them on each new search.
const goalFocus = computed(() => ({
  key: `${goal.value}|${country.value}`,
  ids:
    !loading.value && (goal.value || country.value)
      ? shownUniversities.value
          .filter((u) => (goal.value ? u.goal_matches > 0 : u.faculty > 0))
          .map((u) => u.id)
      : [],
}));

const summary = computed(() => {
  if (loading.value)
    return goal.value ? `Searching for “${goal.value}”` : "Loading";
  const n = shownUniversities.value.filter((u) =>
    goal.value ? u.goal_matches > 0 : u.faculty > 0,
  ).length;
  const people = goal.value
    ? shownUniversities.value.reduce((s, u) => s + u.goal_matches, 0)
    : shownUniversities.value.reduce((s, u) => s + u.faculty, 0);
  const g = grants.value.length;
  const grantText = grantsLoading.value
    ? ""
    : `, ${g >= 40 ? "40+" : g} ${includePastGrants.value ? "" : "active "}${g === 1 ? "grant" : "grants"}`;
  const unis = `${n} ${n === 1 ? "university" : "universities"}`;
  // Person-level filters only apply to the faculty list (the university counts aren't filtered by them).
  if (
    tab.value === "faculty" &&
    (onlyFunded.value ||
      onlyEarly.value ||
      onlyR1.value ||
      onlyNewLab.value ||
      country.value)
  ) {
    const f = faculty.value.length;
    return `${f >= 60 ? "60+" : f} ${f === 1 ? "person matches" : "people match"} your filters${goal.value ? ` for “${goal.value}”` : ""}`;
  }
  if (onlyFunded.value) return `${unis} with faculty holding an active grant`;
  return goal.value
    ? `${people.toLocaleString()} faculty at ${unis} work on this${grantText}`
    : `${people.toLocaleString()} faculty at ${unis}`;
});

function openUniversity(id: string | null, professor: string | null = null) {
  openUni.value = id;
  openProf.value = professor;
}

function openProfessorFromList(name: string, universityId?: string | null) {
  const person = faculty.value.find((f) => f.name === name);
  openUniversity(universityId ?? person?.university_id ?? null, name);
}

function clearAll() {
  selectedAreas.value = [];
  clearGoal();
}

const tabs = computed<{ id: Tab; label: string }[]>(() =>
  goal.value
    ? [
        { id: "faculty", label: "Faculty" },
        { id: "funding", label: "Funding" },
        { id: "universities", label: "Universities" },
      ]
    : [
        { id: "universities", label: "Universities" },
        { id: "faculty", label: "Faculty" },
      ],
);

const about = ref<HTMLDialogElement | null>(null);
const shortlist = ref<InstanceType<typeof ShortlistDialog> | null>(null);
const pickerOpen = ref(false);

function removeArea(area: string) {
  selectedAreas.value = selectedAreas.value.filter((a) => a !== area);
}
</script>

<template>
  <div class="shell">
    <header class="top">
      <h1>Advisor Atlas</h1>
      <form class="search" role="search" @submit.prevent="submitGoal">
        <label class="visually-hidden" for="goal"
          >What do you want to research?</label
        >
        <input
          id="goal"
          v-model="goalInput"
          type="search"
          enterkeyhint="search"
          autocomplete="off"
          placeholder="What do you want to research? For example: mechanistic interpretability"
        />
        <button type="submit">Search</button>
      </form>
      <button type="button" class="your-list" @click="shortlist?.open()">
        Your list<template v-if="saved.length"> ({{ saved.length }})</template>
      </button>
      <button
        type="button"
        class="info"
        aria-label="About the data"
        title="About the data"
        @click="about?.showModal()"
      >
        i
      </button>
    </header>

    <div class="filters">
      <button
        type="button"
        class="filter-btn"
        :class="{ on: pickerOpen }"
        :aria-expanded="pickerOpen"
        aria-controls="area-picker"
        @click="pickerOpen = !pickerOpen"
      >
        Research areas<template v-if="selectedAreas.length">
          ({{ selectedAreas.length }})</template
        >
      </button>
      <span
        v-for="a in selectedAreas"
        :key="a"
        class="chip"
        :style="{ '--c': LINE_COLOR[areaIndex.get(a)?.group ?? ''] }"
      >
        {{ areaIndex.get(a)?.name ?? a }}
        <button
          type="button"
          :aria-label="`Remove ${areaIndex.get(a)?.name ?? a}`"
          @click="removeArea(a)"
        >
          ×
        </button>
      </span>
      <span v-if="!selectedAreas.length" class="filter-hint">All areas</span>
      <span v-if="goal" class="goal-chip">
        Results for <strong>“{{ goal }}”</strong>&nbsp;
        <button type="button" class="link" @click="clearGoal">
          Clear search
        </button>
      </span>
    </div>

    <div v-if="pickerOpen" id="area-picker" class="picker-pop">
      <p v-if="!areas.length" class="hint">Loading areas</p>
      <AreaPicker v-else v-model="selectedAreas" :areas="areas" />
      <div class="picker-actions">
        <button
          v-if="selectedAreas.length"
          type="button"
          class="link"
          @click="selectedAreas = []"
        >
          Clear areas
        </button>
        <button type="button" class="done" @click="pickerOpen = false">
          Done
        </button>
      </div>
    </div>

    <section v-show="!openUni" class="results" aria-label="Results">
      <template v-if="ready && !goal && !selectedAreas.length">
        <p class="intro">
          Search for what you want to research to find professors working on it,
          the grants funding that work, and the universities where they are.
          Narrow by research area at any time.
        </p>
        <p class="examples">
          <span>Try:</span>
          <button
            v-for="q in EXAMPLES"
            :key="q"
            type="button"
            class="example"
            @click="trySearch(q)"
          >
            {{ q }}
          </button>
        </p>
      </template>
      <p class="summary" aria-live="polite">
        {{ summary
        }}<template v-if="selectedNames.length">
          in {{ selectedNames.join(", ") }}</template
        >.
        <button
          v-if="selectedAreas.length || goal"
          type="button"
          class="link"
          @click="clearAll"
        >
          Clear all
        </button>
      </p>
      <p v-if="error && ready" class="error">{{ error }}</p>
      <p v-if="!ready && !error" class="hint">Loading</p>

      <div v-if="ready" class="tabs" role="tablist">
        <button
          v-for="t in tabs"
          :key="t.id"
          role="tab"
          type="button"
          :aria-selected="tab === t.id"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </div>

      <div v-if="ready" class="narrow">
        <label>
          <span class="visually-hidden">Country</span>
          <select v-model="country">
            <option value="">All countries</option>
            <option v-for="c in countryOptions" :key="c.code" :value="c.code">
              {{ c.name }} ({{ c.count }})
            </option>
          </select>
        </label>
        <label v-if="tab !== 'funding'" class="check"
          ><input v-model="onlyFunded" type="checkbox" /> Active grant</label
        >
        <label v-if="tab === 'faculty'" class="check"
          ><input v-model="onlyEarly" type="checkbox" /> Early career</label
        >
        <label
          v-if="tab === 'faculty'"
          class="check"
          title="Holds a running grant for PIs starting out: NSF CAREER, ERC Starting, ARC DECRA, NIH R00, ..."
          ><input v-model="onlyNewLab" type="checkbox" /> New lab, funded</label
        >
        <label v-if="tab !== 'funding'" class="check"
          ><input v-model="onlyR1" type="checkbox" /> R1 (US)</label
        >
        <label v-if="tab === 'faculty'">
          <span class="visually-hidden">Sort</span>
          <select v-model="sortBy">
            <option value="">{{ goal ? "Best match" : "Most active" }}</option>
            <option value="recent">Most papers lately</option>
            <option value="funding">Newest grant</option>
          </select>
        </label>
        <button
          v-if="filtersOn"
          type="button"
          class="link"
          @click="clearFilters"
        >
          Clear filters
        </button>
      </div>
      <p
        v-if="ready && tab === 'faculty' && onlyEarly"
        class="hint narrow-hint"
      >
        Early career: first top-venue paper in the last six years (computer
        science faculty only). New faculty are often building a lab and
        recruiting.
      </p>
      <p
        v-if="ready && country && !fundersFor(country).length && onlyFunded"
        class="hint narrow-hint"
      >
        There's no grant data for {{ countryName(country) }} yet, so "Active
        grant" hides everyone there.
      </p>
      <p v-if="ready && countryNote && tab !== 'funding'" class="country-note">
        {{ countryNote }}
      </p>

      <ol v-if="ready && tab === 'universities'" class="uni-list">
        <li v-for="u in rankedUniversities" :key="u.id">
          <button
            type="button"
            :class="{ on: u.id === openUni }"
            @click="openUniversity(u.id)"
          >
            <span class="uni-name">{{ u.name }}</span>
            <span v-if="u.carnegie" class="r-badge">{{ u.carnegie }}</span>
            <span class="uni-meta">
              <template v-if="goal">{{ u.goal_matches }} matching, </template>
              {{ u.faculty }}
              {{ selectedAreas.length ? "in your areas" : "faculty" }},
              <template v-if="fundersFor(u.country).length"
                >{{ u.funded }} funded</template
              >
              <template v-else>no grant data</template>
            </span>
          </button>
        </li>
      </ol>

      <FundingView
        v-else-if="ready && tab === 'funding'"
        :goal="goal"
        :country="country"
        @open-university="openUniversity($event)"
        @open-person="openProfessorFromList"
        @counts="fundingCounts = $event"
        :grants="grants"
        :grants-loading="grantsLoading"
        :only-active="!includePastGrants"
        @update:only-active="includePastGrants = !$event"
      />

      <ul v-else-if="ready" class="fac-list">
        <FacultyRow
          v-for="f in faculty"
          :key="f.name"
          :person="f"
          :selected-areas="selectedAreas"
          show-university
          @open="openProfessorFromList"
        />
      </ul>

      <footer class="foot">
        Data from CSRankings, DBLP, OpenAlex, IPEDS and public grant records
        (NSF, NIH, NSERC, ARC, Marsden, UKRI, ANR, SNSF, NWO, ERC, KAKEN, RGC).
        <button type="button" class="link" @click="about?.showModal()">
          About the data
        </button>
        <a class="link" href="/overview.html">Project overview</a>
      </footer>
    </section>

    <div class="map-wrap">
      <div v-if="!ready" class="loader" role="status">
        <template v-if="error && !universities.length">
          <p class="loader-text">{{ error }}</p>
          <button type="button" class="retry" @click="retry">Try again</button>
        </template>
        <template v-else>
          <div class="loader-lines" aria-hidden="true">
            <span style="--c: var(--line-ai)"></span>
            <span style="--c: var(--line-systems)"></span>
            <span style="--c: var(--line-theory)"></span>
            <span style="--c: var(--line-inter)"></span>
          </div>
          <p class="loader-text">Loading universities and faculty</p>
        </template>
      </div>
      <MapView
        v-else
        :universities="mapUniversities"
        :color="mapColor"
        :use-goal="!!goal"
        :goal-label="fundingMap ? 'grants on this search' : undefined"
        :selected-id="openUni"
        :focus="goalFocus"
        @select="openUniversity($event)"
      />
      <p v-if="ready" class="legend">
        Dot size:
        {{
          fundingMap
            ? "grants on this search"
            : goal
              ? "faculty matching your search"
              : "faculty in your areas"
        }}. Heavy ring: R1 university.
      </p>
    </div>

    <UniversityDrawer
      v-if="openUni"
      :id="openUni"
      class="drawer-slot"
      :query="query"
      :professor="openProf"
      @close="openUniversity(null)"
      @open-professor="openProf = $event"
    />

    <ShortlistDialog
      ref="shortlist"
      @open-person="openProfessorFromList"
      @open-university="openUniversity($event)"
    />

    <dialog ref="about" class="about">
      <h2>About the data</h2>
      <p>
        <strong>Faculty and research areas</strong> come from
        <a href="https://csrankings.org" target="_blank" rel="noopener"
          >CSRankings</a
        >: computer science faculty and their papers at top venues. Areas count
        papers from the last 10 years.
      </p>
      <p>
        <strong>Grants</strong> come from public records: NSF (US, 2010–2025),
        NIH (US, active projects), Canada's NSERC (2022–2024 payments), the
        Australian Research Council, New Zealand's Marsden Fund, UKRI's EPSRC
        (UK), ANR (France), the Swiss National Science Foundation, the Dutch
        Research Council NWO (all fields, since 2016), the European Research
        Council (Horizon 2020 and Horizon Europe), Japan's KAKEN and Hong Kong's
        Research Grants Council. Outside the US and the Netherlands, only
        computing-related grants are loaded. A grant is linked to a professor
        only when the name matches and the university (or, for NSF, the email
        domain) confirms it. Funding from industry, other agencies and
        universities isn't included, so "no active grant" doesn't mean "no
        funding".
      </p>
      <p class="sources">
        Sources: NSF Award Search; Australian Research Council; Royal Society Te
        Apārangi (Marsden Fund); UKRI Gateway to Research, Open Government
        Licence v2.0; Agence nationale de la recherche, ODbL; Swiss National
        Science Foundation; CORDIS, European Commission; ERC lists of principal
        investigators. Japanese grants: created by Advisor Atlas, based on KAKEN
        (NII), with a link to each project. Hong Kong grants: Research Grants
        Council project records (facts only). Canadian grants: NSERC Awards
        Data; contains information licensed under the Open Government Licence –
        Canada. Dutch grants: NWOpen API (CC0). Researchers outside computer
        science, Pakistani universities beyond LUMS, and paper abstracts:
        OpenAlex (CC0); campus locations © OpenStreetMap contributors (ODbL).
        Scholarships: curated, plus the DAAD scholarship database.
      </p>
      <p>
        <strong>Recent papers</strong> come from
        <a href="https://dblp.org" target="_blank" rel="noopener">DBLP</a>.
      </p>
      <p>
        <strong>University facts</strong> (R1/R2, graduate tuition and
        enrollment) come from the US Department of Education's IPEDS survey, so
        they're shown for US universities only.
      </p>
      <p>
        Search compares the meaning of what you type with each professor's grant
        abstracts and paper titles, and favours recent work. It's a starting
        point: read a professor's own page and recent papers before writing to
        them.
      </p>
      <form method="dialog"><button class="close-about">Close</button></form>
    </dialog>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 1fr var(--drawer-w);
  grid-template-rows: auto auto 1fr;
  grid-template-areas:
    "top top"
    "filters filters"
    "map side";
  height: 100vh;
  height: 100dvh;
  position: relative;
}

.top {
  grid-area: top;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 20px;
  background: var(--ink);
  color: #fff;
}

h1 {
  font-size: var(--t-lg);
  font-weight: 800;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.search {
  flex: 1;
  max-width: 760px;
  display: flex;
}

.search input {
  flex: 1;
  min-width: 0;
  border: 0;
  border-radius: var(--radius-box) 0 0 var(--radius-box);
  padding: 9px 13px 8px;
  font-size: var(--t-md);
  color: var(--ink);
  background: #fff;
}

.search input:focus-visible {
  outline: 3px solid var(--line-ai);
  outline-offset: 0;
}

.search button {
  border: 0;
  border-radius: 0 var(--radius-box) var(--radius-box) 0;
  background: var(--line-ai);
  color: #fff;
  font-weight: 800;
  padding: 0 18px;
}

.your-list {
  margin-left: auto;
  border: 1.5px solid #8794a3;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  font-weight: 700;
  font-size: var(--t-xs);
  padding: 4px 12px 3px;
  white-space: nowrap;
  cursor: pointer;
}

.info {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1.5px solid #8794a3;
  background: transparent;
  color: #fff;
  font-weight: 800;
  font-size: var(--t-xs);
  padding: 2px 0 0;
  flex: none;
}

.filters {
  grid-area: filters;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
  padding: 8px 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--rule);
  min-height: 46px;
}

.filter-btn {
  white-space: nowrap;
  border: 1.5px solid var(--ink);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 3px 12px 2px;
  font-size: var(--t-xs);
  font-weight: 800;
}

.filter-btn.on {
  background: var(--ink);
  color: #fff;
}

.chip {
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--c);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 3px 4px 2px 10px;
  font-size: var(--t-xs);
  font-weight: 700;
}

.chip button {
  border: 0;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  line-height: 1;
  padding: 0;
  font-size: 0.85rem;
}

.filter-hint {
  font-size: var(--t-xs);
  color: var(--ink-faint);
}

.goal-chip {
  margin-left: auto;
  font-size: var(--t-xs);
}

.picker-pop {
  position: absolute;
  z-index: 20;
  top: var(--picker-top, 104px);
  left: 12px;
  width: min(720px, calc(100vw - 24px));
  max-height: calc(100vh - 130px);
  overflow-y: auto;
  background: var(--surface);
  border-radius: var(--radius-box);
  box-shadow: 0 6px 28px rgba(29, 42, 58, 0.25);
  padding: 16px 18px 12px;
}

.picker-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 14px;
  margin-top: 12px;
}

.done {
  border: 0;
  background: var(--ink);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 4px 16px 3px;
  font-weight: 700;
}

.results {
  grid-area: side;
  overflow-y: auto;
  background: var(--surface);
  border-left: 1px solid var(--rule);
  padding: 16px 22px 20px;
  display: flex;
  flex-direction: column;
}

.intro {
  font-size: var(--t-md);
  line-height: 1.5;
  margin-bottom: 12px;
}

.examples {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: -4px 0 14px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.example {
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: #fff;
  padding: 3px 10px 2px;
  font: inherit;
  color: var(--ink);
  cursor: pointer;
}

.example:hover {
  border-color: var(--ink);
}

.country-note {
  margin: 4px 0 8px;
  font-size: var(--t-xs);
  line-height: 1.5;
  color: var(--ink-soft);
}

.hint {
  margin-top: 6px;
  font-size: var(--t-xs);
  color: var(--ink-faint);
}

.summary {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.link {
  border: 0;
  background: none;
  padding: 0;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.tabs {
  display: flex;
  gap: 4px;
  margin: 14px 0 4px;
  border-bottom: 2px solid var(--ink);
}

.tabs button {
  border: 0;
  background: none;
  padding: 6px 12px 4px;
  font-weight: 700;
  color: var(--ink-soft);
  border-radius: var(--radius-box) var(--radius-box) 0 0;
}

.tabs button[aria-selected="true"] {
  background: var(--ink);
  color: #fff;
}

.narrow {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: center;
  margin: 10px 0 4px;
  font-size: var(--t-xs);
  font-weight: 600;
}

.narrow select {
  font: inherit;
  padding: 4px 6px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-box);
  background: #fff;
  color: var(--ink);
  max-width: 190px;
}

.narrow .check {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  white-space: nowrap;
}

.narrow-hint {
  margin: 2px 0 6px;
}

.toggle {
  display: flex;
  gap: 7px;
  align-items: center;
  margin: 10px 0 2px;
  font-size: var(--t-xs);
  font-weight: 600;
}

.uni-list,
.fac-list {
  margin: 0;
  padding: 0;
}

.uni-list li {
  list-style: none;
  border-bottom: 1px solid var(--rule);
}

.uni-list button {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 10px;
  width: 100%;
  text-align: left;
  border: 0;
  background: none;
  padding: 10px 6px 10px 0;
}

.uni-list button:hover .uni-name,
.uni-list button.on .uni-name {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.uni-name {
  font-weight: 700;
}

.r-badge {
  align-self: start;
  border: 2px solid var(--ink);
  border-radius: var(--radius-pill);
  padding: 0 7px;
  font-size: 0.75rem;
  font-weight: 800;
}

.uni-meta {
  grid-column: 1 / -1;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.foot {
  margin-top: auto;
  padding-top: 18px;
  font-size: 0.75rem;
  color: var(--ink-faint);
}

.foot .link {
  font-weight: 600;
  color: var(--ink-soft);
}

.foot .link + .link {
  margin-left: 12px;
}

.map-wrap {
  grid-area: map;
  position: relative;
  min-height: 0;
}

.loader {
  height: 100%;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 14px;
  background: #e9edec;
  padding: 24px;
  text-align: center;
}

.loader-lines {
  display: grid;
  gap: 7px;
  width: 180px;
}

/* The four area lines draw in, one after another. */
.loader-lines span {
  height: 5px;
  border-radius: 3px;
  background: var(--c);
  transform-origin: left;
  animation: draw 1.6s ease-in-out infinite;
}
.loader-lines span:nth-child(2) {
  animation-delay: 0.15s;
}
.loader-lines span:nth-child(3) {
  animation-delay: 0.3s;
}
.loader-lines span:nth-child(4) {
  animation-delay: 0.45s;
}

@keyframes draw {
  0% {
    transform: scaleX(0);
  }
  45%,
  70% {
    transform: scaleX(1);
  }
  100% {
    transform: scaleX(1);
    opacity: 0;
  }
}

.loader-text {
  font-weight: 700;
  color: var(--ink-soft);
  max-width: 40ch;
}

.retry {
  border: 1.5px solid var(--ink);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 4px 14px 3px;
  font-weight: 700;
}

.legend {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: var(--radius-box);
  padding: 5px 10px 4px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.drawer-slot {
  grid-area: side;
  min-height: 0;
}

.error {
  margin-top: 8px;
  color: var(--danger);
  font-weight: 600;
}

.about {
  max-width: 560px;
  border: 0;
  border-radius: var(--radius-box);
  padding: 24px 26px;
  color: var(--ink);
  line-height: 1.55;
}

.about::backdrop {
  background: rgba(29, 42, 58, 0.45);
}

.about h2 {
  font-size: var(--t-lg);
  font-weight: 800;
  margin-bottom: 12px;
}

.about p + p {
  margin-top: 10px;
}

.about .sources {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.close-about {
  margin-top: 18px;
  border: 1.5px solid var(--ink);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 4px 14px 3px;
  font-weight: 700;
}

/* Phones and narrow windows: search, filters, map, then results; drawer covers the screen. */
@media (max-width: 900px) {
  .shell {
    display: flex;
    flex-direction: column;
    height: auto;
  }

  .top {
    flex-wrap: wrap;
    gap: 8px 12px;
    padding: 10px 14px;
  }

  .search {
    order: 3;
    flex-basis: 100%;
    max-width: none;
  }

  .filters {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 8px 14px;
  }

  .goal-chip {
    white-space: nowrap;
  }

  .map-wrap {
    order: 1;
    height: 42vh;
  }

  .results {
    order: 2;
    overflow: visible;
    border-left: 0;
    border-top: 1px solid var(--rule);
    padding: 14px 14px 20px;
  }

  .picker-pop {
    position: fixed;
    inset: 0;
    width: auto;
    max-height: none;
    border-radius: 0;
  }

  .legend {
    font-size: 0.75rem;
    top: 8px;
    left: 8px;
  }

  .drawer-slot {
    position: fixed;
    inset: 0;
    z-index: 10;
  }
}
</style>
