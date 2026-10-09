<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { api, type Landscape } from "@/api";
import LoadingRows from "@/components/LoadingRows.vue";
import {
  approxUSD,
  formatMoney,
  grantYears as years,
  KIND_LABEL,
  niceName,
  short,
  titleLanguage,
  webUrl,
} from "@/lines";
import { funderName } from "@/store";
import { countryName } from "@/countries";

// "Where the money goes" for a search: every grant loaded, whether or not its people are on the map,
// narrowed by funder, kind of grant (new labs, PhD funding) and people in Advisor Atlas; one list of
// grants, sortable. Shown a little at a time: one sentence, then short lists that open up.
const props = defineProps<{
  goal: string;
  country?: string;
  onlyActive: boolean;
}>();
const emit = defineEmits<{
  openUniversity: [id: string];
  openPerson: [name: string, universityId: string | null];
  counts: [byUniversity: Record<string, number> | null];
  "update:onlyActive": [value: boolean];
}>();
const onlyActive = computed(() => props.onlyActive);
const funder = ref("");
const kind = ref<"" | "new_lab" | "training">("");
const peopleOnly = ref(false);
const sortBy = ref<"" | "newest" | "largest">("");
// The funder menu lists the funders of the unfiltered view, so choosing one doesn't empty the menu.
const funderOptions = ref<Landscape["funders"]>([]);
const narrowed = computed(
  () => !!(funder.value || kind.value || peopleOnly.value),
);
function clearNarrowing() {
  funder.value = "";
  kind.value = "";
  peopleOnly.value = false;
}
// A new topic or country starts from every funder (a funder chosen before may fund none of it).
watch(
  () => [props.goal, props.country ?? ""],
  () => (funder.value = ""),
);
const data = ref<Landscape | null>(null);
const loading = ref(false);
const error = ref("");
const showAllFunders = ref(false);
const showAllPlaces = ref(false);
const showAllGrants = ref(false);
let inflight: AbortController | null = null;

watch(
  () =>
    [
      props.goal,
      props.country ?? "",
      onlyActive.value,
      funder.value,
      kind.value,
      peopleOnly.value,
      sortBy.value,
    ] as const,
  async ([goal, country, active, fund, k, people, sort]) => {
    inflight?.abort();
    const mine = (inflight = new AbortController());
    loading.value = true;
    error.value = "";
    try {
      data.value = await api.landscape(
        { goal, country, active, funder: fund, kind: k, people, sort },
        mine.signal,
      );
      if (!fund) funderOptions.value = data.value.funders;
      emit("counts", data.value.by_university);
    } catch (e) {
      if ((e as Error).name !== "AbortError")
        error.value = (e as Error).message;
    } finally {
      // Only the latest request ends the loading state: a cancelled one finishing after a new one
      // started left the panel blank (not loading, no data).
      if (inflight === mine) loading.value = false;
    }
  },
  { immediate: true },
);

const funders = computed(
  () =>
    (showAllFunders.value
      ? data.value?.funders
      : data.value?.funders.slice(0, 4)) ?? [],
);
const maxFunder = computed(() =>
  Math.max(1, ...(data.value?.funders ?? []).map((f) => f.grants)),
);
// CAREER is a signal (see "New lab, funded"), not a topic programme.
const programs = computed(() =>
  (data.value?.programs ?? [])
    // 3+ grants: one-off NSF programmes ("Global Venture Fund", 1 grant) were noise on other topics
    .filter((p) => !p.name.startsWith("CAREER") && p.grants >= 3)
    .slice(0, 5),
);
const places = computed(
  () =>
    (showAllPlaces.value
      ? data.value?.places
      : data.value?.places.slice(0, 8)) ?? [],
);
const grants = computed(
  () =>
    (showAllGrants.value
      ? data.value?.grants
      : data.value?.grants.slice(0, 8)) ?? [],
);

// Grants started per year. NIH is left out: only its running projects are loaded, so its history
// would look like a sudden boom.
const thisYear = new Date().getFullYear();
const trend = computed(() => {
  const by = new Map<number, number>();
  for (const y of data.value?.years ?? [])
    if (y.funder !== "nih") by.set(y.year, (by.get(y.year) ?? 0) + y.grants);
  const years = [...by.keys()];
  // Too few grants make a noisy chart, not a trend.
  if (years.length < 3 || [...by.values()].reduce((a, b) => a + b, 0) < 20)
    return [];
  const out = [];
  for (let y = Math.min(...years); y <= thisYear; y++)
    out.push({ year: y, n: by.get(y) ?? 0 });
  return out;
});
const trendMax = computed(() => Math.max(1, ...trend.value.map((t) => t.n)));

const COMPANY =
  /\b(inc|llc|ltd|limited|corp|corporation|gmbh|sas|s\.a\.)\b\.?/i;
function isCompany(s: string) {
  return COMPANY.test(s);
}
</script>

<template>
  <div class="funding">
    <div class="controls">
      <label class="toggle"
        ><input
          :checked="onlyActive"
          type="checkbox"
          @change="
            emit(
              'update:onlyActive',
              ($event.target as HTMLInputElement).checked,
            )
          "
        />
        Only grants running now</label
      >
      <label>
        <span class="visually-hidden">Funder</span>
        <select v-model="funder">
          <option value="">Every funder</option>
          <option
            v-if="funder && !funderOptions.some((f) => f.funder === funder)"
            :value="funder"
          >
            {{ funderName(funder) }}
          </option>
          <option v-for="f in funderOptions" :key="f.funder" :value="f.funder">
            {{ funderName(f.funder) }} ({{ f.grants.toLocaleString() }})
          </option>
        </select>
      </label>
      <label>
        <span class="visually-hidden">Kind of grant</span>
        <select v-model="kind">
          <option value="">Every kind of grant</option>
          <option value="new_lab">New labs (early-career PIs)</option>
          <option value="training">Funds PhD students</option>
        </select>
      </label>
      <label class="toggle"
        ><input v-model="peopleOnly" type="checkbox" /> Only people in Advisor
        Atlas</label
      >
      <button
        v-if="narrowed"
        type="button"
        class="link clear"
        @click="clearNarrowing"
      >
        Clear filters
      </button>
    </div>
    <LoadingRows
      v-if="loading && !data"
      label="Searching every grant loaded"
      :rows="5"
    />
    <p v-else-if="error" class="error">{{ error }}</p>

    <template v-else-if="data">
      <LoadingRows v-if="loading" bar label="Updating" />
      <p class="lead-line" :class="{ dim: loading }">
        <template v-if="!goal">
          <strong>{{ data.total.toLocaleString() }}</strong>
          {{ onlyActive ? "running grants" : "grants" }} from
          {{ data.funders.length }} funders<template v-if="country">
            in {{ countryName(country) }}</template
          ><template v-if="!onlyActive"
            >, {{ data.active.toLocaleString() }} running now</template
          ><template v-if="data.amount_usd"
            >, ≈ {{ formatMoney(data.amount_usd, "USD") }} in all</template
          >. Search for a topic to see who funds it.
        </template>
        <template v-else-if="!data.total"
          >No grant
          {{ data.matched === "meaning" ? "is about" : "mentions" }} “{{
            goal
          }}”. Try fewer or broader words.</template
        >
        <template v-else>
          <strong>{{ data.total.toLocaleString() }}</strong>
          {{ onlyActive ? "running " : ""
          }}{{ data.total === 1 ? "grant" : "grants" }}
          {{
            data.matched === "meaning"
              ? data.total === 1
                ? "is about"
                : "are about"
              : data.total === 1
                ? "mentions"
                : "mention"
          }}
          “{{ goal }}”<template v-if="country">
            in {{ countryName(country) }}</template
          ><template v-if="!onlyActive"
            >, {{ data.active.toLocaleString() }} running now</template
          ><template v-if="data.amount_usd"
            >, ≈ {{ formatMoney(data.amount_usd, "USD") }} in all</template
          >.<template v-if="!peopleOnly">
            This counts every grant loaded, including those whose researchers
            aren't in Advisor Atlas.</template
          >
        </template>
      </p>

      <section v-if="data.funders.length">
        <h3>Who pays</h3>
        <ul class="bars">
          <li v-for="f in funders" :key="f.funder">
            <button
              type="button"
              class="name link"
              :title="`Only ${funderName(f.funder)}'s grants`"
              @click="funder = funder === f.funder ? '' : f.funder"
            >
              {{ funderName(f.funder) }}
            </button>
            <span class="bar"
              ><span
                :style="{ width: `${(100 * f.grants) / maxFunder}%` }"
              ></span
            ></span>
            <span class="num">{{ f.grants }}</span>
            <span class="sub">
              {{ f.active }} running<template v-if="f.amount"
                >, {{ formatMoney(f.amount, f.currency ?? "USD") }} in
                all<template v-if="approxUSD(f.amount_usd, f.currency)">
                  ({{ approxUSD(f.amount_usd, f.currency) }})</template
                ></template
              >
            </span>
          </li>
        </ul>
        <button
          v-if="data.funders.length > 4"
          type="button"
          class="link more"
          @click="showAllFunders = !showAllFunders"
        >
          {{
            showAllFunders
              ? "Fewer funders"
              : `All ${data.funders.length} funders`
          }}
        </button>
      </section>

      <section v-if="programs.length">
        <h3>NSF programmes that fund this</h3>
        <p class="hint">
          As NSF names them. Search a name on nsf.gov for its current call and
          deadlines.
        </p>
        <ul class="programs">
          <li v-for="p in programs" :key="p.name">
            <span>{{ p.name }}</span>
            <span class="sub"
              >{{ p.grants }} {{ p.grants === 1 ? "grant" : "grants" }},
              {{ p.running }} running</span
            >
          </li>
        </ul>
      </section>

      <section v-if="trend.length">
        <h3>Grants started each year</h3>
        <div
          class="trend"
          role="img"
          :aria-label="`Grants started per year, ${trend[0].year} to ${thisYear}`"
        >
          <span
            v-for="t in trend"
            :key="t.year"
            :style="{ height: `${Math.max(2, (100 * t.n) / trendMax)}%` }"
            :class="{ partial: t.year === thisYear }"
            :title="`${t.year}: ${t.n}`"
          ></span>
        </div>
        <p class="axis">
          <span>{{ trend[0].year }}</span
          ><span>{{ thisYear }} (so far)</span>
        </p>
      </section>

      <section v-if="data.places.length">
        <h3>Where the money goes</h3>
        <p class="hint">
          Institutions holding the most of these grants. A lab with a running
          grant is often hiring.
        </p>
        <ol class="places">
          <li
            v-for="p in places"
            :key="p.institution + (p.university_id ?? '')"
          >
            <button
              v-if="p.university_id"
              type="button"
              class="link"
              @click="emit('openUniversity', p.university_id)"
            >
              {{ niceName(p.institution) }}
            </button>
            <span v-else class="plain"
              >{{ niceName(p.institution)
              }}<span v-if="isCompany(p.institution)" class="tag"
                >company</span
              ></span
            >
            <span class="sub">
              {{ p.grants }} {{ p.grants === 1 ? "grant" : "grants" }},
              {{ p.active }} running<template v-if="p.people"
                >, {{ p.people }} {{ p.people === 1 ? "lead" : "leads" }} in
                Advisor Atlas</template
              >
            </span>
          </li>
        </ol>
        <button
          v-if="data.places.length > 8"
          type="button"
          class="link more"
          @click="showAllPlaces = !showAllPlaces"
        >
          {{ showAllPlaces ? "Fewer" : `Top ${data.places.length}` }}
        </button>
      </section>

      <section v-if="data.grants.length" class="grant-list">
        <div class="list-head">
          <h3>
            {{ goal ? `Grants about “${goal}”` : "Grants" }}
          </h3>
          <label>
            <span class="visually-hidden">Sort grants</span>
            <select v-model="sortBy">
              <option value="">{{ goal ? "Best match" : "Newest" }}</option>
              <option value="newest">Newest</option>
              <option value="largest">Largest</option>
            </select>
          </label>
        </div>
        <ul class="grants">
          <li v-for="g in grants" :key="g.funder + g.id">
            <a
              v-if="webUrl(g.url)"
              :href="webUrl(g.url)"
              target="_blank"
              rel="noopener"
              class="title"
              >{{ g.title }}</a
            >
            <span v-else class="title">{{ g.title }}</span>
            <p class="sub">
              <span v-if="g.signal" class="kind" :class="g.signal">{{
                KIND_LABEL[g.signal]
              }}</span>
              <span v-if="titleLanguage(g.title)" class="lang">{{
                titleLanguage(g.title)
              }}</span>
              {{ funderName(g.funder)
              }}<template v-if="g.amount"
                >, {{ formatMoney(g.amount, g.currency ?? "USD")
                }}<template v-if="approxUSD(g.amount_usd, g.currency)">
                  ({{ approxUSD(g.amount_usd, g.currency) }})</template
                ></template
              >, {{ years(g) }}
            </p>
            <p v-if="g.lead" class="sub">
              <button
                v-if="g.profile"
                type="button"
                class="link"
                @click="emit('openPerson', g.profile, g.university_id)"
              >
                {{ short(g.profile) }}</button
              ><span v-else>{{ g.lead }}</span
              ><template v-if="g.institution"
                >, {{ niceName(g.institution) }}</template
              ><span v-if="g.profile" class="in-atlas">in Advisor Atlas</span>
            </p>
            <details v-if="g.snippet">
              <summary>Summary</summary>
              <p>{{ g.snippet }}&hellip;</p>
            </details>
          </li>
        </ul>
        <button
          v-if="data.grants.length > 8"
          type="button"
          class="link more"
          @click="showAllGrants = !showAllGrants"
        >
          {{ showAllGrants ? "Fewer grants" : `Show ${data.grants.length}` }}
        </button>
      </section>
      <p v-else-if="narrowed" class="hint">
        No grant matches these filters.
        <button type="button" class="link" @click="clearNarrowing">
          Clear filters
        </button>
      </p>

      <p class="hint coverage">
        {{
          data.matched === "meaning"
            ? "Matched on the meaning of each grant's title and summary, and on its words."
            : "Matched on the words in each grant's title and summary."
        }}
        From KAKEN, ARC, ANR, SNSF, ERC, UKRI (EPSRC), NSERC, Marsden and RGC
        only computing grants are loaded; the other funders' cover every field.
        NIH lists running projects only, NSFC's list ends in 2021, and 28
        funders come through OpenAlex. Dollar amounts are approximate, at fixed
        exchange rates.
      </p>
    </template>
  </div>
</template>

<style scoped>
.funding {
  display: grid;
  gap: 18px;
  padding-top: 4px;
}

.toggle {
  display: flex;
  gap: 7px;
  align-items: center;
  margin-top: 8px;
  font-size: var(--t-xs);
  font-weight: 600;
}

.lead-line {
  font-size: var(--t-md);
  line-height: 1.45;
}

.lead-line.dim {
  opacity: 0.55;
}

h3 {
  font-size: var(--t-sm);
  font-weight: 800;
  padding-bottom: 5px;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 8px;
}

.hint {
  font-size: var(--t-xs);
  color: var(--ink-faint);
  margin: -2px 0 8px;
}

.bars,
.places,
.grants {
  margin: 0;
  padding: 0;
  list-style: none;
}

.bars li {
  display: grid;
  grid-template-columns: 70px 1fr 48px;
  gap: 4px 10px;
  align-items: center;
  padding: 4px 0;
  font-size: var(--t-sm);
}

.bars .name {
  font-weight: 700;
  text-align: left;
  padding: 0;
}

.bar {
  height: 8px;
  background: var(--rule);
  border-radius: 999px;
  overflow: hidden;
}

.bar span {
  display: block;
  height: 100%;
  background: var(--line-ai);
}

.bars .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.bars .sub {
  grid-column: 2 / 4;
  margin-top: -2px;
}

.sub {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}

.trend {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 64px;
}

.trend span {
  flex: 1;
  background: var(--ink-soft);
  border-radius: 2px 2px 0 0;
}

.trend span.partial {
  background: var(--rule-strong);
}

.axis {
  display: flex;
  justify-content: space-between;
  font-size: var(--t-xs);
  color: var(--ink-faint);
  margin-top: 4px;
}

.programs {
  margin: 0;
  padding: 0;
  list-style: none;
}

.programs li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  font-size: var(--t-sm);
  border-bottom: 1px solid var(--rule);
}

.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 14px;
}

.controls .toggle {
  margin-top: 0;
}

.controls select,
.list-head select {
  font: inherit;
  font-size: var(--t-xs);
  padding: 4px 6px;
  border: 1px solid var(--rule);
  border-radius: var(--radius-box);
  background: var(--surface);
  max-width: 100%;
}

.controls .clear {
  font-size: var(--t-xs);
}

.list-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 10px;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 8px;
}

.list-head h3 {
  border-bottom: 0;
  margin-bottom: 0;
}

.list-head label {
  padding-bottom: 5px;
}

.kind,
.lang,
.in-atlas {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  border-radius: var(--radius-pill);
  padding: 0 7px;
  margin-right: 6px;
  vertical-align: 1px;
}

.kind.new_lab {
  background: #e3f1e6;
  color: #1f6b35;
}

.kind.training {
  background: #e6eefb;
  color: #24508f;
}

.lang {
  background: #f1efe8;
  color: var(--ink-soft);
}

.in-atlas {
  margin: 0 0 0 6px;
  background: #eef0f3;
  color: var(--ink-soft);
  font-weight: 600;
}

.places li {
  display: grid;
  gap: 1px;
  padding: 6px 0;
  border-bottom: 1px solid var(--rule);
}

.plain {
  font-weight: 700;
}

.tag {
  margin-left: 6px;
  font-size: var(--t-xs);
  font-weight: 600;
  color: var(--ink-faint);
}

.grants li {
  padding: 10px 0;
  border-bottom: 1px solid var(--rule);
  display: grid;
  gap: 3px;
}

.grants .title {
  font-weight: 700;
  line-height: 1.35;
}

details summary {
  font-size: var(--t-xs);
  color: var(--ink-soft);
  cursor: pointer;
}

details p {
  font-size: var(--t-xs);
  line-height: 1.5;
  color: var(--ink-soft);
  margin-top: 4px;
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

.more {
  margin-top: 6px;
  font-size: var(--t-xs);
}

.coverage {
  margin-top: 4px;
}
</style>
