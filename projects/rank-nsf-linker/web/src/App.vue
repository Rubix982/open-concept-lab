<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { api, type Faculty, type Query, type UniversitySummary } from "@/api";
import { INK_HEX, LINE_COLOR, LINE_HEX } from "@/lines";
import { areaIndex, areas, funderName, funders, fundersFor } from "@/store";
import { countryName } from "@/countries";
import AreaPicker from "@/components/AreaPicker.vue";
import FacultyRow from "@/components/FacultyRow.vue";
import FundingView from "@/components/FundingView.vue";
import ShortlistDialog from "@/components/ShortlistDialog.vue";
import TourGuide, { type TourStep } from "@/components/TourGuide.vue";
import LoadingRows from "@/components/LoadingRows.vue";
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

// Navigation (a search, a tab, a university or a profile opened) adds a history entry, so the
// browser's Back and Forward move through it; filter changes only rewrite the current entry.
let restoring = false;
let lastNav = "";
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
    const nav = JSON.stringify([
      goal.value,
      tab.value,
      openUni.value,
      openProf.value,
    ]);
    const target = s ? `?${s}` : location.pathname;
    if (!restoring && lastNav && nav !== lastNav)
      history.pushState(null, "", target);
    else history.replaceState(null, "", target); // first load (an old ?view=grants becomes funding)
    lastNav = nav;
  },
  { immediate: true },
);

// Back / Forward: put the page back the way that history entry had it.
window.addEventListener("popstate", () => {
  const q = new URLSearchParams(location.search);
  restoring = true;
  selectedAreas.value = q.get("areas")?.split(",").filter(Boolean) ?? [];
  goal.value = goalInput.value = q.get("q") ?? "";
  const view = (q.get("view") ?? "").replace("grants", "funding");
  tab.value = (
    ["faculty", "funding"].includes(view) ? view : "universities"
  ) as Tab;
  openUni.value = q.get("u");
  openProf.value = q.get("p");
  country.value = q.get("country") ?? "";
  onlyFunded.value = q.get("funded") === "1";
  onlyEarly.value = q.get("early") === "1";
  onlyR1.value = q.get("r1") === "1";
  onlyNewLab.value = q.get("newlab") === "1";
  sortBy.value = (
    ["recent", "funding"].includes(q.get("sort") ?? "") ? q.get("sort") : ""
  ) as Sort;
  nextTick(() => (restoring = false));
});

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
}

// ---- data ----
const universities = ref<UniversitySummary[]>([]);
const faculty = ref<Faculty[]>([]);
const loadedGoal = ref<string | null>(null); // the search the current lists were loaded for
// A different search is loading: the lists on screen belong to the previous one (unrelated people
// under "Searching for …" read as wrong results), so placeholders replace them. A filter change on
// the same search keeps the list, dimmed.
const newSearch = computed(
  () => loading.value && (query.value.goal ?? "") !== (loadedGoal.value ?? ""),
);
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
    loadedGoal.value = query.value.goal;
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

onMounted(loadAreas);
watch([query, filterParams], load, { immediate: true, deep: true });

// ---- derived ----
// Names for the summary line, with whole fields as one name (see areaChips).
const selectedNames = computed(() => areaChips.value.map((c) => c.label));

// Dots take the line colour when every chosen area is on one line.
const mapColor = computed(() => {
  const groups = new Set(
    selectedAreas.value.map((a) => areaIndex.value.get(a)?.group),
  );
  return groups.size === 1
    ? (LINE_HEX[[...groups][0] ?? ""] ?? INK_HEX)
    : INK_HEX;
});

// Every country with universities listed, for the map's shading (filters don't change it).
const listedCountries = computed(() => [
  ...new Set(universities.value.map((u) => u.country ?? "").filter(Boolean)),
]);

// On the Funding tab the dots show money (grants on the search) instead of people.
const fundingCounts = ref<Record<string, number> | null>(null);
const fundingMap = computed(
  () => tab.value === "funding" && !!fundingCounts.value,
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
    ? `${people.toLocaleString()} faculty at ${unis} work on this`
    : `${people.toLocaleString()} faculty at ${unis}`;
});

function openUniversity(id: string | null, professor: string | null = null) {
  openUni.value = id;
  openProf.value = professor;
}

// From a profile's university name: that university's page, and the map moved to it (also when the
// profile was opened from the same university, so the map would not move on its own).
const mapView = ref<InstanceType<typeof MapView> | null>(null);
function showUniversity(id: string) {
  openUniversity(id);
  nextTick(() => mapView.value?.flyToUniversity(id));
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
        { id: "funding", label: "Funding" },
      ],
);

const about = ref<HTMLDialogElement | null>(null);

// ---- guided tour (?tour=1 starts it, e.g. from a shared link or for a recording) ----
const touring = ref(url.get("tour") === "1");
const TOUR_GOAL = "robot learning";
const TOUR_UNIVERSITY = "universitymichigan";
async function until(ok: () => boolean, ms = 12000) {
  const end = Date.now() + ms;
  while (!ok() && Date.now() < end)
    await new Promise((r) => setTimeout(r, 150));
}
async function tourSearch() {
  pickerOpen.value = false;
  clearFilters();
  selectedAreas.value = [];
  if (goal.value !== TOUR_GOAL) trySearch(TOUR_GOAL);
  openUniversity(null);
  tab.value = "faculty";
  // Wait for the lists of this search, not the ones already on screen from before it.
  await until(
    () =>
      !loading.value &&
      loadedGoal.value === TOUR_GOAL &&
      faculty.value.length > 0,
  );
}
const tourSteps: TourStep[] = [
  {
    title: "Find a PhD advisor, step by step",
    body: "Advisor Atlas shows who is researching what you want to study, how their work is funded, and where they are. This short tour uses a real search; you can leave at any time with Esc.",
  },
  {
    target: ".search",
    title: "Say what you want to research",
    body: `Type it in your own words: a topic, a method, a problem. The tour searches for “${TOUR_GOAL}”.`,
    before: () => {
      openUniversity(null);
      goalInput.value = TOUR_GOAL;
    },
  },
  {
    target: ".fac-list",
    title: "People working on it",
    body: "Faculty and researchers whose recent papers and grants are closest in meaning to your search, newest work first. “New lab, funded” marks someone starting a lab with money: they are usually recruiting students.",
    before: tourSearch,
  },
  {
    target: ".narrow",
    title: "Narrow it down",
    body: "Choose a country, or show only people with an active grant, early in their career, or starting a funded lab. Sort by recent papers or newest grant.",
    before: tourSearch,
  },
  {
    target: ".prof",
    ready: ".prof header h2",
    title: "A professor's page",
    body: "What they are working on now, their papers closest to your search, their grants and who they work with. Names link to other profiles.",
    before: async () => {
      await tourSearch();
      const first = faculty.value[0];
      if (first) openProfessorFromList(first.name, first.university_id);
    },
  },
  {
    target: ".prof .before",
    title: "Before you write",
    body: "Which paper to read first, how their work fits yours, and what to ask about funding. Tick the items as you go; the ticks stay in your browser.",
  },
  {
    target: ".prof .save",
    title: "Save to your list",
    body: "Keep professors and universities to compare side by side later, in “Your list” at the top.",
  },
  {
    target: ".funding",
    title: "Where the money goes",
    body: "Who pays for this topic, whether it is growing, and which universities hold the grants, counting every grant loaded, even those of researchers not on the map. The map's dots now show money, not people. Open Funding without a search for the whole picture.",
    before: async () => {
      await tourSearch();
      tab.value = "funding";
    },
  },
  {
    target: ".drawer-slot",
    title: "A university",
    body: "Its research strengths, PhDs awarded (US), who funds its faculty, funded PhD programmes that pay students directly, and scholarships you can apply for.",
    before: () => {
      tab.value = "universities";
      openUniversity(TOUR_UNIVERSITY);
    },
  },
  {
    target: ".your-list",
    title: "Over to you",
    body: "Try your own search. Your saved professors and universities are under “Your list”, and the tour is always in the (i) menu.",
    before: () => openUniversity(null),
  },
];
// The tour is offered (header button, intro link) until someone has started it once; after that it
// lives in the (i) menu. Remembered in this browser only.
const TOUR_KEY = "atlas.tourSeen";
const tourSeen = ref(false);
try {
  tourSeen.value = localStorage.getItem(TOUR_KEY) === "1";
} catch {
  /* storage blocked: keep offering it */
}
function startTour() {
  shortlist.value?.close();
  about.value?.close();
  infoOpen.value = false;
  touring.value = true;
  tourSeen.value = true;
  try {
    localStorage.setItem(TOUR_KEY, "1");
  } catch {
    /* fine */
  }
}
const infoOpen = ref(false);
function endTour() {
  touring.value = false;
}
const shortlist = ref<InstanceType<typeof ShortlistDialog> | null>(null);
const pickerOpen = ref(false);

function removeArea(...remove: string[]) {
  selectedAreas.value = selectedAreas.value.filter((a) => !remove.includes(a));
}

// The areas a student can pick; the rest only name a person's tags.
const pickableAreas = computed(() => areas.value.filter((a) => a.listed));

// Chosen areas as chips: a field whose subfields are all chosen ("All of Neuroscience") is one chip.
const areaChips = computed(() => {
  const chosen = new Set(selectedAreas.value);
  const byField = new Map<string, string[]>();
  for (const a of pickableAreas.value)
    if (a.field)
      byField.set(a.field, [...(byField.get(a.field) ?? []), a.area]);
  const chips: {
    key: string;
    label: string;
    group: string;
    areas: string[];
  }[] = [];
  const covered = new Set<string>();
  for (const [field, list] of byField) {
    if (list.length > 1 && list.every((a) => chosen.has(a))) {
      chips.push({
        key: `field:${field}`,
        label: `${field} (all)`,
        group: areaIndex.value.get(list[0])?.group ?? "",
        areas: list,
      });
      list.forEach((a) => covered.add(a));
    }
  }
  for (const a of selectedAreas.value) {
    if (!covered.has(a)) {
      chips.push({
        key: a,
        label: areaIndex.value.get(a)?.name ?? a,
        group: areaIndex.value.get(a)?.group ?? "",
        areas: [a],
      });
    }
  }
  return chips;
});
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
      <button
        type="button"
        class="filter-btn"
        :class="{ on: pickerOpen }"
        :aria-expanded="pickerOpen"
        aria-controls="area-picker"
        @click="pickerOpen = !pickerOpen"
      >
        <span class="wide">Research areas</span
        ><span class="narrow-label">Areas</span
        ><template v-if="selectedAreas.length">
          ({{ selectedAreas.length }})</template
        >
      </button>
      <button
        v-if="!tourSeen"
        type="button"
        class="tour-btn"
        @click="startTour"
      >
        Tour
      </button>
      <button type="button" class="your-list" @click="shortlist?.open()">
        Your list<template v-if="saved.length"> ({{ saved.length }})</template>
      </button>
      <span class="row-break" aria-hidden="true" />
      <div class="info-wrap">
        <button
          type="button"
          class="info"
          aria-label="About Advisor Atlas"
          title="About Advisor Atlas"
          :aria-expanded="infoOpen"
          aria-controls="info-menu"
          @click="infoOpen = !infoOpen"
        >
          i
        </button>
        <div
          v-if="infoOpen"
          id="info-menu"
          class="info-menu"
          @keydown.esc="infoOpen = false"
        >
          <button type="button" class="link" @click="startTour">
            Take the tour
          </button>
          <button
            type="button"
            class="link"
            @click="
              infoOpen = false;
              about?.showModal();
            "
          >
            About the data
          </button>
          <a class="link" href="/overview.html">Project overview</a>
          <p>
            Data from CSRankings, DBLP, OpenAlex, IPEDS and public grant records
            from 42 funders.
          </p>
        </div>
      </div>
    </header>
    <div v-if="infoOpen" class="info-scrim" @click="infoOpen = false" />

    <div v-if="pickerOpen" id="area-picker" class="picker-pop">
      <p v-if="!areas.length" class="hint">Loading areas</p>
      <AreaPicker v-else v-model="selectedAreas" :areas="pickableAreas" />
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
          <button
            v-if="!tourSeen"
            type="button"
            class="link"
            @click="startTour"
          >
            Take the tour
          </button>
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
          v-if="goal && tab !== 'funding' && !loading"
          type="button"
          class="link funding-link"
          @click="tab = 'funding'"
        >
          See who funds this
        </button>
        <button
          v-if="selectedAreas.length || goal"
          type="button"
          class="link"
          @click="clearAll"
        >
          Clear all
        </button>
      </p>
      <p
        v-if="ready && !goal && tab !== 'funding' && funders.totals"
        class="funding-teaser"
      >
        <strong>{{ funders.totals.grants.toLocaleString() }}</strong> research
        grants from {{ funders.totals.funders }} funders,
        {{ funders.totals.running.toLocaleString() }} running now.
        <button type="button" class="link" @click="tab = 'funding'">
          Explore the funding
        </button>
      </p>
      <p v-if="areaChips.length" class="area-chips">
        <span
          v-for="c in areaChips"
          :key="c.key"
          class="chip"
          :style="{ '--c': LINE_COLOR[c.group] }"
        >
          {{ c.label }}
          <button
            type="button"
            :aria-label="`Remove ${c.label}`"
            @click="removeArea(...c.areas)"
          >
            ×
          </button>
        </span>
      </p>
      <p v-if="error && ready" class="error">{{ error }}</p>
      <LoadingRows
        v-if="!ready && !error && tab !== 'funding'"
        label="Loading universities and faculty"
        :rows="6"
      />

      <div v-if="ready || areas.length" class="tabs" role="tablist">
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

      <p
        v-if="
          ready &&
          !loading &&
          tab === 'universities' &&
          !rankedUniversities.length
        "
        class="empty"
      >
        No university matches<template v-if="goal"> “{{ goal }}”</template> with
        these filters. Try broader words, or
        <button
          type="button"
          class="link"
          @click="
            clearAll();
            clearFilters();
          "
        >
          start over</button
        >.
      </p>
      <LoadingRows
        v-if="ready && newSearch && tab !== 'funding'"
        :label="goal ? `Searching for “${goal}”` : 'Loading'"
        :rows="6"
      />
      <LoadingRows
        v-else-if="ready && loading && tab !== 'funding'"
        bar
        :label="goal ? `Searching for “${goal}”` : 'Updating'"
      />
      <ol
        v-if="ready && !newSearch && tab === 'universities'"
        class="uni-list"
        :class="{ stale: loading }"
      >
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
        v-else-if="areas.length && tab === 'funding'"
        :goal="goal"
        :country="country"
        @open-university="openUniversity($event)"
        @open-person="openProfessorFromList"
        @counts="fundingCounts = $event"
        :only-active="!includePastGrants"
        @update:only-active="includePastGrants = !$event"
      />

      <ul
        v-else-if="ready && !newSearch && tab === 'faculty'"
        class="fac-list"
        :class="{ stale: loading }"
      >
        <FacultyRow
          v-for="f in faculty"
          :key="f.name"
          :person="f"
          :selected-areas="selectedAreas"
          show-university
          @open="openProfessorFromList"
        />
      </ul>
      <p
        v-if="ready && !loading && tab === 'faculty' && !faculty.length"
        class="empty"
      >
        No one matches<template v-if="goal"> “{{ goal }}”</template> with these
        filters. Try broader words, or
        <button
          type="button"
          class="link"
          @click="
            clearAll();
            clearFilters();
          "
        >
          start over</button
        >.
      </p>
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
        :use-goal="!!goal || fundingMap"
        :goal-label="
          fundingMap ? (goal ? 'grants on this search' : 'grants') : undefined
        "
        :countries="listedCountries"
        ref="mapView"
        :selected-id="openUni"
        :focus="goalFocus"
        @select="openUniversity($event)"
      />
      <p v-if="ready" class="legend">
        Dot size:
        {{
          fundingMap
            ? goal
              ? "grants on this search"
              : "grants"
            : goal
              ? "faculty matching your search"
              : "faculty in your areas"
        }}. Heavy ring: R1 university.
        <br />
        <span class="swatch" style="background: #bcd6b0"></span> Grant data
        loaded <span class="swatch" style="background: #dde8d2"></span> Listed,
        no grant data yet
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
      @open-university="showUniversity($event)"
    />

    <TourGuide v-if="touring" :steps="tourSteps" @end="endTour" />

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
        <strong>Grants</strong> come from public records of 42 funders. Loaded
        directly: NSF (US, 2010 onward), NIH (US, active projects), Canada's
        NSERC, the Australian Research Council, New Zealand's Marsden Fund,
        UKRI's EPSRC (UK), ANR (France), the Swiss National Science Foundation,
        the Dutch Research Council NWO, the European Research Council, Japan's
        KAKEN, Hong Kong's Research Grants Council and Austria's FWF and Korea's
        NRF. Through OpenAlex: 28 national and provincial funders, among them
        China's NSFC, Taiwan's NSTC, Canada's CIHR and SSHRC, Brazil's FAPESP,
        Turkey's TÜBİTAK, Sweden's research councils, Israel's ISF, Wellcome and
        Pakistan's HEC (NRPU). From KAKEN, ARC, ANR, SNSF, ERC, UKRI, NSERC,
        Marsden and RGC only computing-related grants are loaded; from the
        others, every field (grants running in 2015 or later). A grant is linked
        to a person only when the name matches and the university (or, for NSF,
        the email domain) confirms it; Chinese names are compared in pinyin.
        Funding from industry, other agencies and universities isn't included,
        so "no active grant" doesn't mean "no funding".
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
        Canada. Dutch grants: NWOpen API (CC0). Austrian grants: FWF Open API
        (CC0). National funders via OpenAlex awards (CC0; each funder's own
        terms apply). Australian health grants: National Health and Medical
        Research Council (CC BY 4.0). Flemish grants: FRIS, Flemish Government.
        Polish grants: Narodowe Centrum Nauki, retrieved October 2026 (dates
        estimated from NCN's call calendar). Japanese medical grants:
        出典：国立研究開発法人日本医療研究開発機構 (AMED). Indian grants: Indian
        Council of Medical Research. Brazilian grants: Biblioteca Virtual da
        FAPESP. Swedish grants: SweCRIS. Danish grants: Research Portal Denmark.
        Korean grants: National Research Foundation of Korea, via data.go.kr.
        Spanish (ISCIII) and Sri Lankan grants are shown as facts and links
        only. Researchers outside computer science, Pakistani universities
        beyond LUMS, and paper abstracts: OpenAlex (CC0); campus locations ©
        OpenStreetMap contributors (ODbL). Scholarships: curated, plus the DAAD
        scholarship database.
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
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "top top"
    "map side";
  height: 100vh;
  height: 100dvh;
  position: relative;
}

.top {
  grid-area: top;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 7px 16px;
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

.tour-btn {
  border: 0;
  background: none;
  color: #fff;
  font-weight: 700;
  font-size: var(--t-xs);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
  white-space: nowrap;
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

.row-break {
  display: none;
}

.info-wrap {
  position: relative;
  flex: none;
}

.info-menu {
  position: absolute;
  z-index: 30;
  right: 0;
  top: calc(100% + 8px);
  width: 250px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 9px;
  padding: 14px 16px;
  background: var(--surface);
  color: var(--ink);
  border-radius: var(--radius-box);
  box-shadow: 0 6px 28px rgba(29, 42, 58, 0.25);
  font-size: var(--t-xs);
}

.info-menu .link {
  font-weight: 700;
  color: var(--ink);
}

.info-menu p {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 0.75rem;
}

.info-scrim {
  position: fixed;
  inset: 0;
  z-index: 25;
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

.filter-btn {
  white-space: nowrap;
  border: 1.5px solid #8794a3;
  color: #fff;
  background: transparent;
  border-radius: var(--radius-pill);
  padding: 3px 12px 2px;
  font-size: var(--t-xs);
  font-weight: 800;
}

.filter-btn .narrow-label {
  display: none;
}

.filter-btn.on {
  background: #fff;
  color: var(--ink);
  border-color: #fff;
}

.area-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: -4px 0 12px;
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

.picker-pop {
  position: absolute;
  z-index: 20;
  top: var(--picker-top, 52px);
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

.funding-link {
  margin-right: 10px;
}

.funding-teaser {
  margin: -6px 0 14px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.stale {
  opacity: 0.45;
  transition: opacity 0.2s;
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

.empty {
  margin: 14px 0;
  font-size: var(--t-sm);
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

.legend .swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin: 0 3px 0 6px;
  border: 1px solid #5d6876;
  border-radius: 2px;
  vertical-align: -1px;
}

.legend .swatch:first-of-type {
  margin-left: 0;
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
    flex: 1 1 0;
    min-width: 0;
    max-width: none;
  }

  .row-break {
    display: block;
    order: 2;
    flex-basis: 100%;
    height: 0;
  }

  /* Phones: title, tour, list and (i) on the first row; search and areas on the second */
  .filter-btn {
    order: 4;
    flex: none;
    padding: 6px 12px 5px;
  }

  .filter-btn .wide {
    display: none;
  }

  .filter-btn .narrow-label {
    display: inline;
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
