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
import { areaIndex, areas as allAreas, funderName } from "@/store";
import FacultyRow from "./FacultyRow.vue";
import ProfessorView from "./ProfessorView.vue";
import UniversityGrants from "./UniversityGrants.vue";
import TabSearch from "./TabSearch.vue";
import LoadingRows from "@/components/LoadingRows.vue";

const props = defineProps<{
  id: string;
  query: Query;
  professor: string | null;
}>();
const emit = defineEmits<{
  close: [];
  openProfessor: [name: string | null];
  openUniversity: [id: string];
}>();

const uni = ref<UniversityDetail | null>(null);
const faculty = ref<Faculty[]>([]);
const loading = ref(true); // the faculty list
const uniLoading = ref(true); // the university's details
const error = ref("");

// The Faculty tab's own search and filters, starting from the page's search
const facQ = ref(props.query.goal);
const facFunded = ref(false);
const facNewLab = ref(false);
const facSort = ref<"" | "recent" | "funding">("");
const facName = ref(""); // narrows the loaded list by name, in the browser
// An area or a field picked from the tab's summary: the list shows only its people
const facAreas = ref<string[] | null>(null);
const facAreaLabel = ref("");
function pickArea(area: string, label: string) {
  const same = facAreaLabel.value === label;
  facAreas.value = same ? null : [area];
  facAreaLabel.value = same ? "" : label;
}
const OPENALEX_GROUP_NAMES = new Set([
  "Sciences",
  "Engineering",
  "Medicine",
  "Social sciences & humanities",
]);
function pickField(field: string) {
  if (facAreaLabel.value === field) {
    facAreas.value = null;
    facAreaLabel.value = "";
    return;
  }
  // the field's own area and its subfields
  facAreas.value = allAreas.value
    .filter(
      (a) =>
        a.field === field ||
        (!a.field && a.name === field && OPENALEX_GROUP_NAMES.has(a.group)),
    )
    .map((a) => a.area);
  facAreaLabel.value = field;
}
function unpick() {
  facAreas.value = null;
  facAreaLabel.value = "";
}
const fieldsAll = ref(false);
const fieldList = computed(() =>
  fieldsAll.value
    ? (uni.value?.fields ?? [])
    : (uni.value?.fields ?? []).slice(0, 10),
);
const facNarrowed = computed(
  () =>
    !!facQ.value ||
    facFunded.value ||
    facNewLab.value ||
    !!facName.value ||
    !!facAreas.value,
);
function clearFaculty() {
  facAreas.value = null;
  facAreaLabel.value = "";
  facQ.value = "";
  facFunded.value = false;
  facNewLab.value = false;
  facName.value = "";
}
watch(
  () => [props.id, props.query.goal],
  () => {
    facQ.value = props.query.goal;
    facFunded.value = false;
    facNewLab.value = false;
    facSort.value = "";
    facName.value = "";
    facAreas.value = null;
    facAreaLabel.value = "";
    fieldsAll.value = false;
  },
);

let loadSeq = 0;
async function load() {
  const seq = ++loadSeq; // switching universities quickly: only the latest answer is shown
  uniLoading.value = true;
  error.value = "";
  try {
    const detail = await api.university(props.id);
    if (seq === loadSeq) uni.value = detail;
  } catch (e) {
    if (seq === loadSeq) error.value = (e as Error).message;
  } finally {
    if (seq === loadSeq) uniLoading.value = false;
  }
}
watch(() => props.id, load, { immediate: true });

let facSeq = 0;
async function loadFaculty() {
  const seq = ++facSeq;
  loading.value = true;
  try {
    const people = await api.faculty({
      areas: facAreas.value ?? props.query.areas,
      goal: facQ.value,
      university: props.id,
      limit: 150,
      funded: facFunded.value ? 1 : undefined,
      newlab: facNewLab.value ? 1 : undefined,
      sort: facSort.value || undefined,
    });
    if (seq === facSeq) faculty.value = people;
  } catch (e) {
    if (seq === facSeq) error.value = (e as Error).message;
  } finally {
    if (seq === facSeq) loading.value = false;
  }
}
// One key for everything the list depends on, so a change of university (which also resets the
// filters) asks once, not once per changed filter
const facultyKey = computed(() =>
  JSON.stringify([
    props.id,
    facAreas.value ?? props.query.areas,
    facQ.value,
    facFunded.value,
    facNewLab.value,
    facSort.value,
  ]),
);
const fold = (t: string) =>
  t
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
const shownFaculty = computed(() =>
  facName.value
    ? faculty.value.filter((f) => fold(f.name).includes(fold(facName.value)))
    : faculty.value,
);

// Scholarships for studying in this university's country; students check eligibility on each programme's page.
const scholarships = ref<Scholarship[]>([]);

// The page in tabs, so no list runs on forever: Faculty first when the visit comes from a search
// (that's what was asked for), else the overview.
type UniTab = "overview" | "faculty" | "funding" | "scholarships";
const uniTab = ref<UniTab>("overview");
const facultyShown = ref(10);
watch(
  facultyKey,
  () => {
    facultyShown.value = 10;
    loadFaculty();
  },
  { immediate: true },
);
watch(
  () => props.id,
  () => {
    uniTab.value = props.query.goal ? "faculty" : "overview";
    facultyShown.value = 10;
  },
  { immediate: true },
);
const uniTabs = computed<{ id: UniTab; label: string }[]>(() => [
  { id: "overview", label: "Overview" },
  {
    id: "faculty",
    label: `Faculty${uni.value ? ` ${uni.value.faculty_total.toLocaleString("en-US")}` : ""}`,
  },
  { id: "funding", label: "Funding" },
  {
    id: "scholarships",
    label: `Scholarships${scholarships.value.length ? ` ${scholarships.value.length}` : ""}`,
  },
]);
// A level to narrow by: only levels that narrow the list are offered. When every programme covers
// every level (China's two cover Master's and PhD), the buttons changed nothing and looked broken.
const schLevel = ref("");
const atLevelCount = (l: string) =>
  scholarships.value.filter((s) => s.levels.includes(l)).length;
const schLevels = computed(() =>
  ["masters", "phd", "postdoc"].filter(
    (l) => atLevelCount(l) > 0 && atLevelCount(l) < scholarships.value.length,
  ),
);
// A new list (another country): the level chosen for the last one may not be offered here.
watch(scholarships, () => (schLevel.value = ""));
const atLevel = (s: Scholarship) =>
  !schLevel.value || s.levels.includes(schLevel.value);
// The tab's own search (name, provider, what it covers, notes) and order, in the browser
const schQ = ref("");
const schSort = ref<"window" | "name">("window");
watch(scholarships, () => (schQ.value = ""));
const schMatch = (s: Scholarship) =>
  !schQ.value ||
  fold(
    [s.name, s.provider, s.covers, s.notes, s.application_window].join(" "),
  ).includes(fold(schQ.value));

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

const byName = (a: Scholarship, b: Scholarship) => a.name.localeCompare(b.name);
const curatedScholarships = computed(() =>
  scholarships.value
    .filter((s) => s.source !== "daad" && atLevel(s) && schMatch(s))
    .sort(schSort.value === "name" ? byName : byWindow),
);
const feedScholarships = computed(() =>
  scholarships.value
    .filter((s) => s.source === "daad" && atLevel(s) && schMatch(s))
    .sort(schSort.value === "name" ? byName : () => 0),
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
const OPENALEX_GROUPS = new Set([
  "Sciences",
  "Engineering",
  "Medicine",
  "Social sciences & humanities",
]);
const strengths = computed(() => {
  const entries = Object.entries(uni.value?.area_faculty ?? {})
    .filter(
      ([area]) => !OPENALEX_GROUPS.has(areaIndex.value.get(area)?.group ?? ""),
    )
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
      @university="(id: string) => emit('openUniversity', id)"
    />

    <div v-else class="uni">
      <p v-if="error" class="error">
        {{
          /not found/i.test(error)
            ? "We couldn't find this university. The link may be old, or the university renamed."
            : error
        }}
        <button type="button" class="link" @click="emit('close')">
          Back to the map
        </button>
      </p>
      <LoadingRows
        v-if="uniLoading && !uni && !error"
        label="Loading the university"
        :rows="5"
      />
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

        <nav class="uni-tabs" role="tablist" aria-label="About this university">
          <button
            v-for="t in uniTabs"
            :key="t.id"
            type="button"
            role="tab"
            :aria-selected="uniTab === t.id"
            :class="{ on: uniTab === t.id }"
            @click="uniTab = t.id"
          >
            {{ t.label }}
          </button>
        </nav>

        <template v-if="uniTab === 'overview'">
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

          <section
            v-if="strengths.length || uni.fields?.length"
            class="strengths"
          >
            <h3>Research strengths</h3>
            <template v-if="strengths.length">
              <p class="sub">
                {{
                  uni.fields?.length
                    ? "Computer science faculty here, by area (the full CSRankings list)"
                    : "Faculty and researchers listed here, by area"
                }}
              </p>
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
            </template>
            <p v-if="uni.fields?.length" class="sub fields-line">
              {{ strengths.length ? "Also here: researchers" : "Researchers" }}
              in {{ uni.fields.length }}
              {{ uni.fields.length === 1 ? "field" : "fields" }}, among them
              {{
                uni.fields
                  .slice(0, 3)
                  .map((f) => f.field)
                  .join(", ")
              }}.
              <button type="button" class="link" @click="uniTab = 'faculty'">
                See them by field
              </button>
            </p>
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
                usually paid as research or teaching assistants, which also
                covers tuition, and faculty with active grants are the ones
                hiring research assistants.
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
                and university budgets that aren't in Advisor Atlas yet. Read
                "no ERC grant" as "no data", not "no funding".
              </p>
            </template>
            <p v-else>
              Grant data for universities in {{ countryLabel }} isn't in Advisor
              Atlas yet, so faculty funding isn't shown. Ask faculty directly
              about funded PhD positions, and see the scholarships below.
            </p>
            <div v-if="uni.training?.length" class="recent training">
              <p class="sub">
                Funded PhD programmes ({{ uni.training.length }}): training
                grants that pay students' stipends and tuition. Apply to the
                programme, not to one professor.
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
            <button type="button" class="to-tab" @click="uniTab = 'funding'">
              See the grants held here
            </button>
          </section>
        </template>

        <UniversityGrants
          v-if="uniTab === 'funding'"
          :university-id="id"
          :goal="query.goal"
          @open-person="(n: string) => emit('openProfessor', n)"
        />

        <section v-if="uniTab === 'scholarships'" class="scholarships">
          <h3>Funding you can apply for</h3>
          <p v-if="!scholarships.length" class="sub">
            No scholarships in our list for study in {{ countryLabel }}.
          </p>
          <template v-else>
            <TabSearch
              v-model="schQ"
              live
              label="Search these scholarships"
              placeholder="Search by name, funder or what it covers"
            />
            <div class="tab-controls">
              <label>
                <span class="visually-hidden">Sort scholarships</span>
                <select v-model="schSort">
                  <option value="window">Opens soonest</option>
                  <option value="name">A to Z</option>
                </select>
              </label>
              <button
                v-if="schQ || schLevel"
                type="button"
                class="clear"
                @click="
                  schQ = '';
                  schLevel = '';
                "
              >
                Clear
              </button>
            </div>
            <p
              v-if="!curatedScholarships.length && !feedScholarships.length"
              class="sub"
            >
              None match. Try another word, or clear the search.
            </p>
          </template>
          <p
            v-if="schLevels.length"
            class="levels"
            role="group"
            aria-label="Level"
          >
            <button
              type="button"
              :class="{ on: !schLevel }"
              @click="schLevel = ''"
            >
              All {{ scholarships.length }}
            </button>
            <button
              v-for="l in schLevels"
              :key="l"
              type="button"
              :class="{ on: schLevel === l }"
              @click="schLevel = l"
            >
              {{ levelLabel([l]) }} {{ atLevelCount(l) }}
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

        <section v-if="uniTab === 'faculty'">
          <h3>
            {{
              facQ
                ? `Faculty whose work matches “${facQ}”`
                : hasAreas
                  ? "Faculty in your areas"
                  : "Faculty"
            }}
          </h3>
          <div v-if="uni.people" class="pglance">
            <dl
              class="pstats"
              :data-audit-ok="
                uni.people.funded ? undefined : 'a 0 here is explained below'
              "
            >
              <div>
                <dt>Listed here</dt>
                <dd>{{ uni.faculty_total.toLocaleString("en-US") }}</dd>
              </div>
              <div>
                <dt>With an active grant</dt>
                <dd>{{ uni.people.funded.toLocaleString("en-US") }}</dd>
              </div>
              <div v-if="uni.people.new_lab">
                <dt>New lab, funded</dt>
                <dd>{{ uni.people.new_lab.toLocaleString("en-US") }}</dd>
              </div>
              <div
                v-if="uni.people.csrankings"
                title="Computer science faculty whose first paper was in the last six years (known only for computer science, from DBLP)"
              >
                <dt>Early-career CS faculty</dt>
                <dd>{{ uni.people.early.toLocaleString("en-US") }}</dd>
              </div>
            </dl>
            <p v-if="!uni.people.funded" class="note zero">
              No one listed here has a running grant in the data Advisor Atlas
              holds for {{ countryLabel
              }}<template v-if="uni.grant_funders?.length">
                ({{
                  uni.grant_funders
                    .map((f) => funderName(f).replace(/\s*\([^)]*\)$/, ""))
                    .join(", ")
                }})</template
              ><template v-else> (none yet)</template>. That usually means the
              funding isn't in our data, not that there is none: ask about
              funded positions when you write.
            </p>

            <template v-if="strengths.length && uni.people.csrankings">
              <p class="cap">
                Computer science, by area ({{ uni.people.csrankings }} faculty,
                the full CSRankings list)
              </p>
              <ul class="pbars">
                <li v-for="a in strengths.slice(0, 6)" :key="a.area">
                  <button
                    type="button"
                    class="pick"
                    :class="{ on: facAreaLabel === a.name }"
                    :aria-pressed="facAreaLabel === a.name"
                    @click="pickArea(a.area, a.name)"
                  >
                    {{ a.name }}
                  </button>
                  <span class="s-track"
                    ><span
                      class="s-fill"
                      :style="{ width: a.width + '%', background: a.color }"
                    ></span
                  ></span>
                  <span class="num">{{ a.n }}</span>
                </li>
              </ul>
            </template>

            <template v-if="uni.fields?.length">
              <p class="cap">
                {{
                  uni.people.csrankings ? "Other fields here" : "Fields here"
                }}
              </p>
              <p
                class="chips"
                data-audit-ok="OpenAlex's sample: up to 20 per field, explained in the note below"
              >
                <button
                  v-for="f in fieldList"
                  :key="f.field"
                  type="button"
                  class="chip"
                  :class="{ on: facAreaLabel === f.field }"
                  :aria-pressed="facAreaLabel === f.field"
                  @click="pickField(f.field)"
                  :title="`${f.people} listed${f.funded ? `, ${f.funded} with an active grant` : ''}`"
                >
                  {{ f.field
                  }}<span v-if="f.people < 20" class="n"> {{ f.people }}</span>
                </button>
                <button
                  v-if="(uni.fields?.length ?? 0) > 10"
                  type="button"
                  class="clear"
                  @click="fieldsAll = !fieldsAll"
                >
                  {{ fieldsAll ? "Fewer" : `All ${uni.fields.length}` }}
                </button>
              </p>
              <p class="note">
                Researchers outside computer science are the most-cited in each
                field here, up to 20 per field (from OpenAlex): these show which
                fields are here, not how big they are. Pick one to list its
                people.
              </p>
            </template>
          </div>

          <TabSearch
            v-model="facQ"
            label="Search this university's faculty"
            placeholder="Search by research topic, e.g. protein design"
          />
          <div class="tab-controls">
            <label>
              <input v-model="facFunded" type="checkbox" />
              Active grant
            </label>
            <label>
              <input v-model="facNewLab" type="checkbox" />
              New lab, funded
            </label>
            <label>
              <span class="visually-hidden">Sort faculty</span>
              <select v-model="facSort">
                <option value="">
                  {{
                    facQ || query.areas.length ? "Best match" : "Most active"
                  }}
                </option>
                <option value="recent">Most papers lately</option>
                <option value="funding">Newest grant</option>
              </select>
            </label>
            <label>
              <span class="visually-hidden">Find a name</span>
              <input
                v-model="facName"
                class="name-filter"
                type="search"
                placeholder="Find a name"
              />
            </label>
            <span v-if="facAreaLabel" class="picked"
              >{{ facAreaLabel }}
              <button
                type="button"
                aria-label="Show every field"
                @click="unpick"
              >
                ×
              </button></span
            >
            <button
              v-if="facNarrowed"
              type="button"
              class="clear"
              @click="clearFaculty"
            >
              Clear
            </button>
          </div>
          <LoadingRows v-if="loading && uni" bar label="Updating faculty" />
          <p v-if="!loading && !shownFaculty.length" class="sub">
            {{
              facName
                ? `No one named “${facName}” among these.`
                : "No faculty here match. Try fewer words, or clear the filters."
            }}
          </p>
          <ul class="list">
            <FacultyRow
              v-for="f in shownFaculty.slice(0, facultyShown)"
              :key="f.name"
              :person="f"
              :selected-areas="query.areas"
              @open="emit('openProfessor', $event)"
            />
          </ul>
          <button
            v-if="shownFaculty.length > facultyShown"
            type="button"
            class="show-more"
            @click="facultyShown += 10"
          >
            Show 10 more ({{ shownFaculty.length - facultyShown }} left)
          </button>
          <p
            v-else-if="uni && !facName && faculty.length < uni.faculty_total"
            class="sub"
          >
            The {{ faculty.length }}
            {{ facQ || hasAreas ? "best matches" : "most active" }} of
            {{ uni.faculty_total.toLocaleString("en-US") }} are listed.
          </p>
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
.fields-line {
  margin-top: 10px;
}
.fields-line .link {
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
.pglance {
  margin: 12px 0 4px;
  padding: 12px 14px;
  border: 1px solid var(--rule);
  border-radius: var(--radius-box);
  background: var(--surface);
}
.pstats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  margin: 0;
}
.pstats dt {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.pstats dd {
  margin: 2px 0 0;
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.pglance .cap {
  margin: 14px 0 6px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.pbars {
  list-style: none;
  margin: 0;
  padding: 0;
}
.pbars li {
  display: grid;
  grid-template-columns: minmax(0, 12em) 1fr 2.5em;
  gap: 10px;
  align-items: center;
  padding: 2px 0;
  font-size: var(--t-xs);
}
.pbars .num {
  text-align: right;
}
.pick {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  text-align: left;
  color: var(--ink);
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pick:hover,
.pick.on {
  text-decoration: underline;
  text-underline-offset: 3px;
}
.pick.on {
  font-weight: 700;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0;
}
.chip {
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: var(--surface);
  padding: 3px 10px 2px;
  font: inherit;
  font-size: var(--t-xs);
  color: var(--ink);
  cursor: pointer;
}
.chip .n {
  margin-left: 5px;
  color: var(--ink-soft);
  font-variant-numeric: tabular-nums;
}
.chip:hover {
  border-color: var(--ink);
}
.chip.on {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
}
.chip.on .n {
  color: #fff;
}
.chips .clear {
  border: 0;
  background: none;
  padding: 0 4px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}
.pglance .note.zero {
  margin: 8px 0 0;
  color: var(--ink-soft);
}
.pglance .note {
  margin: 8px 0 0;
  font-size: var(--t-xs);
  color: var(--ink-faint);
}
.picked {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px 1px 10px;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  font-weight: 700;
}
.picked button {
  border: 0;
  background: none;
  color: #fff;
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
}
.name-filter {
  font: inherit;
  width: 9em;
  padding: 4px 6px;
  border: 1px solid var(--rule);
  border-radius: var(--radius-box);
  background: var(--surface);
}
.uni-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin: 16px 0 4px;
  border-bottom: 1px solid var(--rule);
}
.uni-tabs button {
  padding: 6px 0;
  border: 0;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
  background: none;
  font: inherit;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
}
.uni-tabs button.on {
  color: var(--ink);
  border-bottom-color: var(--ink);
}
.uni-tabs button:focus-visible {
  outline: 2px solid var(--ink);
  outline-offset: 2px;
}
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

/* Opens the Funding tab: a button like "Save to your list", set apart from the lists above */
.to-tab {
  display: block;
  margin-top: 18px;
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: var(--surface, #fff);
  padding: 5px 14px 4px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink);
  cursor: pointer;
}
.to-tab:hover {
  border-color: var(--ink);
}
.to-tab:focus-visible {
  outline: 2px solid var(--ink);
  outline-offset: 2px;
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
