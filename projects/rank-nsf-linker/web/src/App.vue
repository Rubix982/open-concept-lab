<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { api, type Faculty, type Query, type UniversitySummary } from "@/api";
import { INK_HEX, LINE_HEX } from "@/lines";
import { areaIndex, areas } from "@/store";
import AreaPicker from "@/components/AreaPicker.vue";
import FacultyRow from "@/components/FacultyRow.vue";
import MapView from "@/components/MapView.vue";
import UniversityDrawer from "@/components/UniversityDrawer.vue";

// ---- state, mirrored in the URL so a search can be shared ----
const url = new URLSearchParams(location.search);
const selectedAreas = ref<string[]>(url.get("areas")?.split(",").filter(Boolean) ?? []);
const goalInput = ref(url.get("q") ?? "");
const goal = ref(goalInput.value);
const tab = ref<"universities" | "faculty">(url.get("view") === "faculty" ? "faculty" : "universities");
const openUni = ref<string | null>(url.get("u"));
const openProf = ref<string | null>(url.get("p"));

const query = computed<Query>(() => ({ areas: selectedAreas.value, goal: goal.value }));

watch([selectedAreas, goal, tab, openUni, openProf], () => {
  const p = new URLSearchParams();
  if (selectedAreas.value.length) p.set("areas", selectedAreas.value.join(","));
  if (goal.value) p.set("q", goal.value);
  if (tab.value === "faculty") p.set("view", "faculty");
  if (openUni.value) p.set("u", openUni.value);
  if (openProf.value) p.set("p", openProf.value);
  const s = p.toString();
  history.replaceState(null, "", s ? `?${s}` : location.pathname);
});

// The goal box searches after typing pauses.
let goalTimer: number | undefined;
watch(goalInput, (v) => {
  clearTimeout(goalTimer);
  goalTimer = window.setTimeout(() => (goal.value = v.trim()), 450);
});

// ---- data ----
const universities = ref<UniversitySummary[]>([]);
const faculty = ref<Faculty[]>([]);
const loading = ref(true);
const error = ref("");
let inflight: AbortController | null = null;

async function load() {
  inflight?.abort();
  inflight = new AbortController();
  loading.value = true;
  error.value = "";
  try {
    const [u, f] = await Promise.all([
      api.universities(query.value, inflight.signal),
      api.faculty({ ...query.value, limit: 60 }, inflight.signal),
    ]);
    universities.value = u;
    faculty.value = f;
    loading.value = false;
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
    error.value = (e as Error).message;
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    areas.value = await api.areas();
  } catch (e) {
    error.value = (e as Error).message;
  }
});
watch(query, load, { immediate: true, deep: true });

// ---- derived ----
const selectedNames = computed(() =>
  selectedAreas.value.map((a) => areaIndex.value.get(a)?.name ?? a),
);

// Dots take the line colour when every chosen area is on one line.
const mapColor = computed(() => {
  const groups = new Set(selectedAreas.value.map((a) => areaIndex.value.get(a)?.group));
  return groups.size === 1 ? (LINE_HEX[[...groups][0] ?? ""] ?? INK_HEX) : INK_HEX;
});

const rankedUniversities = computed(() =>
  universities.value.filter((u) => (goal.value ? u.goal_matches > 0 : u.faculty > 0)).slice(0, 80),
);

const summary = computed(() => {
  if (loading.value) return "Searching";
  const n = universities.value.filter((u) => (goal.value ? u.goal_matches > 0 : u.faculty > 0)).length;
  const people = goal.value
    ? universities.value.reduce((s, u) => s + u.goal_matches, 0)
    : universities.value.reduce((s, u) => s + u.faculty, 0);
  return goal.value
    ? `${people.toLocaleString()} faculty at ${n} universities have work matching your goal`
    : `${people.toLocaleString()} faculty at ${n} universities`;
});

function openUniversity(id: string | null, professor: string | null = null) {
  openUni.value = id;
  openProf.value = professor;
}

function openProfessorFromList(name: string) {
  const person = faculty.value.find((f) => f.name === name);
  openUniversity(person?.university_id ?? null, name);
}

function clearAll() {
  selectedAreas.value = [];
  goalInput.value = "";
  goal.value = "";
}

const about = ref<HTMLDialogElement | null>(null);
</script>

<template>
  <div class="shell" :class="{ 'has-drawer': openUni }">
    <header class="top">
      <h1>Advisor Atlas</h1>
      <p class="lede">
        Find professors working on what you want to research, read what they're working on now, and see
        whether they have grants that fund PhD students.
      </p>
      <button type="button" class="about-btn" @click="about?.showModal()">About the data</button>
    </header>

    <main class="panel" aria-label="Search">
      <section class="step">
        <h2 class="step-title"><span class="n">1</span> Pick research areas</h2>
        <AreaPicker v-model="selectedAreas" :areas="areas" />
      </section>

      <section class="step">
        <h2 class="step-title"><span class="n">2</span> Describe your research goal</h2>
        <label class="visually-hidden" for="goal">Your research goal</label>
        <textarea
          id="goal"
          v-model="goalInput"
          rows="2"
          placeholder="For example: making large language models explain their answers"
        ></textarea>
        <p class="hint">Matched against professors' NSF grants and recent paper titles. Optional.</p>
      </section>

    </main>

    <section v-show="!openUni" class="results" aria-label="Results">
        <h2 class="step-title"><span class="n">3</span> Compare</h2>
        <p class="summary" aria-live="polite">
          {{ summary }}<template v-if="selectedNames.length"> in {{ selectedNames.join(", ") }}</template>.
          <button v-if="selectedAreas.length || goal" type="button" class="link" @click="clearAll">Clear</button>
        </p>
        <p v-if="error" class="error">{{ error }}</p>

        <div class="tabs" role="tablist">
          <button
            role="tab"
            type="button"
            :aria-selected="tab === 'universities'"
            @click="tab = 'universities'"
          >
            Universities
          </button>
          <button role="tab" type="button" :aria-selected="tab === 'faculty'" @click="tab = 'faculty'">
            Faculty
          </button>
        </div>

        <ol v-if="tab === 'universities'" class="uni-list">
          <li v-for="u in rankedUniversities" :key="u.id">
            <button type="button" :class="{ on: u.id === openUni }" @click="openUniversity(u.id)">
              <span class="uni-name">{{ u.name }}</span>
              <span v-if="u.carnegie" class="r-badge">{{ u.carnegie }}</span>
              <span class="uni-meta">
                <template v-if="goal">{{ u.goal_matches }} matching, </template>
                {{ u.faculty }} {{ selectedAreas.length ? "in your areas" : "faculty" }},
                {{ u.funded }} funded
              </span>
            </button>
          </li>
        </ol>

        <ul v-else class="fac-list">
          <FacultyRow
            v-for="f in faculty"
            :key="f.name"
            :person="f"
            :selected-areas="selectedAreas"
            show-university
            @open="openProfessorFromList"
          />
        </ul>
    </section>

    <div class="map-wrap">
      <MapView
        :universities="universities"
        :color="mapColor"
        :use-goal="!!goal"
        :selected-id="openUni"
        @select="openUniversity($event)"
      />
      <p class="legend">
        Dot size: {{ goal ? "faculty matching your goal" : "faculty in your areas" }}. Heavy ring: R1 university.
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

    <dialog ref="about" class="about">
      <h2>About the data</h2>
      <p>
        <strong>Faculty and research areas</strong> come from
        <a href="https://csrankings.org" target="_blank" rel="noopener">CSRankings</a>: computer science faculty and
        their papers at top venues. Areas count papers from the last 10 years.
      </p>
      <p>
        <strong>Grants</strong> are NSF awards from 2010 to 2025, linked to a professor only when the name matches
        and either the university or the email domain confirms it. Funding from industry, other agencies and
        universities isn't included, so "no active grant" doesn't mean "no funding".
      </p>
      <p><strong>Recent papers</strong> come from <a href="https://dblp.org" target="_blank" rel="noopener">DBLP</a>.</p>
      <p>
        <strong>University facts</strong> (R1/R2, graduate tuition and enrollment) come from the US Department of
        Education's IPEDS survey, so they're shown for US universities only.
      </p>
      <p>
        Goal matching looks for your words in grant abstracts and paper titles. Try different phrasings, and
        always read a professor's own page before writing to them.
      </p>
      <form method="dialog"><button class="close-about">Close</button></form>
    </dialog>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--panel-w) 1fr var(--drawer-w);
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "top top top"
    "panel map side";
  height: 100vh;
  height: 100dvh;
}

.top {
  grid-area: top;
  display: flex;
  align-items: baseline;
  gap: 20px;
  padding: 14px 24px 12px;
  background: var(--ink);
  color: #fff;
}

h1 {
  font-size: var(--t-lg);
  font-weight: 800;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.lede {
  font-size: var(--t-xs);
  color: #c9d1da;
  max-width: 72ch;
}

.about-btn {
  margin-left: auto;
  border: 1.5px solid #6b7887;
  background: transparent;
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 3px 12px 2px;
  font-size: var(--t-xs);
  font-weight: 700;
  white-space: nowrap;
}

.panel {
  grid-area: panel;
  overflow-y: auto;
  background: var(--paper);
  border-right: 1px solid var(--rule);
  padding: 18px 22px 40px;
}

.step + .step {
  margin-top: 20px;
}

.results {
  grid-area: side;
  overflow-y: auto;
  background: var(--surface);
  border-left: 1px solid var(--rule);
  padding: 18px 22px 40px;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: var(--t-md);
  font-weight: 800;
  margin-bottom: 12px;
}

/* Step numbers read as stations along the panel. */
.n {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2.5px solid var(--ink);
  font-size: var(--t-xs);
  font-weight: 800;
  padding-top: 2px;
}

textarea {
  width: 100%;
  resize: vertical;
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--radius-box);
  background: var(--surface);
  padding: 9px 11px;
  line-height: 1.4;
}

textarea:focus-visible {
  outline-offset: 0;
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

.close-about {
  margin-top: 18px;
  border: 1.5px solid var(--ink);
  background: var(--surface);
  border-radius: var(--radius-pill);
  padding: 4px 14px 3px;
  font-weight: 700;
}

/* Phones and narrow windows: map on top, panel below, drawer covers the screen. */
@media (max-width: 900px) {
  .shell {
    display: flex;
    flex-direction: column;
    height: auto;
  }

  .map-wrap {
    order: 1;
  }

  .panel {
    order: 2;
  }

  .results {
    order: 3;
  }

  .map-wrap {
    height: 42vh;
  }

  .panel,
  .results {
    overflow: visible;
  }

  .results {
    border-left: 0;
    border-top: 1px solid var(--rule);
    padding: 16px 16px 40px;
  }

  .legend {
    font-size: 0.75rem;
    top: 8px;
    left: 8px;
  }

  .top {
    flex-wrap: wrap;
    gap: 4px 12px;
    padding: 12px 16px;
  }

  .lede {
    order: 3;
    flex-basis: 100%;
  }

  .panel {
    padding: 16px 16px 40px;
    border-right: 0;
  }

  .drawer-slot {
    position: fixed;
    inset: 0;
    z-index: 10;
  }
}
</style>
