<script setup lang="ts">
// The grants held at one university (its page): how many, how many running, by whom, with the
// tab's own search, sort and filters. Starts from the page's search; the funding search filtered to
// this university (server/landscape.go).
import { computed, ref, watch } from "vue";
import { api, type Landscape } from "@/api";
import LoadingRows from "@/components/LoadingRows.vue";
import TabSearch from "@/components/TabSearch.vue";
import {
  approxUSD,
  formatMoney,
  grantTitle,
  grantYears,
  KIND_LABEL,
  personName,
  short,
  titleLanguage,
  webUrl,
} from "@/lines";
import { funderName, showGrant } from "@/store";

const props = defineProps<{ universityId: string; goal: string }>();
const emit = defineEmits<{ openPerson: [name: string] }>();

const data = ref<Landscape | null>(null);
const loading = ref(false);
const failed = ref(false);
const onlyRunning = ref(false);
const peopleOnly = ref(false); // only grants led by someone with a profile here
const shown = ref(10);
const q = ref(props.goal); // this tab's search
const funder = ref("");
const kind = ref<"" | "new_lab" | "training">("");
const sortBy = ref<"" | "newest" | "largest">("newest"); // "": best match (with a search)
// Funders to choose from: those of the list before a funder was chosen
const funderOptions = ref<Landscape["funders"]>([]);
const narrowed = computed(
  () =>
    !!q.value ||
    onlyRunning.value ||
    peopleOnly.value ||
    !!funder.value ||
    !!kind.value,
);
function clearAll() {
  q.value = "";
  onlyRunning.value = false;
  peopleOnly.value = false;
  funder.value = "";
  kind.value = "";
}
// Another university or a new search on the page: start over from it
watch(
  () => [props.universityId, props.goal],
  () => {
    q.value = props.goal;
    onlyRunning.value = false;
    peopleOnly.value = false;
    funder.value = "";
    kind.value = "";
    funderOptions.value = [];
  },
);
// A search ranks by match unless another order was chosen; clearing it goes back to newest
watch(q, (v, old) => {
  if (v && !old && sortBy.value === "newest") sortBy.value = "";
  if (!v && sortBy.value === "") sortBy.value = "newest";
});
let inflight: AbortController | null = null;

async function load() {
  inflight?.abort();
  const mine = new AbortController();
  inflight = mine;
  loading.value = true;
  failed.value = false;
  try {
    const res = await api.landscape(
      {
        goal: q.value,
        university: props.universityId,
        active: onlyRunning.value,
        people: peopleOnly.value,
        funder: funder.value,
        kind: kind.value,
        sort: sortBy.value,
      },
      mine.signal,
    );
    data.value = res;
    if (!funder.value) funderOptions.value = res.funders;
  } catch (e) {
    if ((e as Error).name !== "AbortError") failed.value = true;
  } finally {
    if (inflight === mine) loading.value = false; // only the latest request clears the spinner
  }
}
watch(
  () => [
    props.universityId,
    q.value,
    onlyRunning.value,
    peopleOnly.value,
    funder.value,
    kind.value,
    sortBy.value,
  ],
  () => {
    shown.value = 10;
    load();
  },
  { immediate: true },
);

const grants = computed(() => data.value?.grants.slice(0, shown.value) ?? []);
const funders = computed(() => (data.value?.funders ?? []).slice(0, 4));
// "grants, 40 running now, from Marsden Fund, NSF and others." (after the bold count)
const summary = computed(() => {
  const d = data.value;
  if (!d) return "";
  let out = d.total === 1 ? "grant" : "grants";
  if (!onlyRunning.value) out += `, ${d.active.toLocaleString()} running now`;
  if (funders.value.length) {
    out += `, from ${funders.value.map((f) => funderName(f.funder)).join(", ")}`;
    if ((d.funders?.length ?? 0) > funders.value.length) out += " and others";
  }
  return out + ".";
});

// At a glance: the money, by funder, and grants started per year, for what's listed (the tab's
// search and filters apply). Approximate US dollars (server/currency.go).
const usdOf = (f: Landscape["funders"][number], amount: number | null) =>
  amount != null && f.amount && f.amount_usd != null
    ? (amount * f.amount_usd) / f.amount
    : null;
const totalUSD = computed(() =>
  (data.value?.funders ?? []).reduce((a, f) => a + (f.amount_usd ?? 0), 0),
);
const runningUSD = computed(() =>
  (data.value?.funders ?? []).reduce(
    (a, f) => a + (usdOf(f, f.active_amount) ?? 0),
    0,
  ),
);
const funderBars = computed(() => {
  const list = (data.value?.funders ?? [])
    .filter((f) => (f.amount_usd ?? 0) > 0)
    .sort((a, b) => (b.amount_usd ?? 0) - (a.amount_usd ?? 0))
    .slice(0, 4);
  const max = Math.max(1, ...list.map((f) => f.amount_usd ?? 0));
  return list.length > 1 || (list.length === 1 && totalUSD.value > 0)
    ? list.map((f) => ({
        funder: f.funder,
        usd: f.amount_usd ?? 0,
        grants: f.grants,
        width: Math.max(3, (100 * (f.amount_usd ?? 0)) / max),
      }))
    : [];
});
// NIH is left out, as on the Funding tab: only its running projects are loaded, so its history
// would look like a sudden boom. Too few grants make a noisy chart, not a trend.
const thisYear = new Date().getFullYear();
const trend = computed(() => {
  const by = new Map<number, number>();
  for (const y of data.value?.years ?? [])
    if (y.funder !== "nih" && y.year >= thisYear - 14)
      by.set(y.year, (by.get(y.year) ?? 0) + y.grants);
  const years = [...by.keys()];
  if (years.length < 3 || [...by.values()].reduce((a, b) => a + b, 0) < 15)
    return [];
  const out = [];
  for (let y = Math.min(...years); y <= thisYear; y++)
    out.push({ year: y, n: by.get(y) ?? 0 });
  return out;
});
const trendMax = computed(() => Math.max(1, ...trend.value.map((t) => t.n)));
const trendLeftOut = computed(() =>
  (data.value?.funders ?? []).some((f) => f.funder === "nih"),
);
</script>

<template>
  <div class="held">
    <TabSearch
      v-model="q"
      label="Search this university's grants"
      placeholder="Search this university's grants, e.g. malaria"
    />
    <div class="tab-controls">
      <label>
        <input v-model="onlyRunning" type="checkbox" />
        Running now
      </label>
      <label
        title="Grants led by someone with a profile in Advisor Atlas, whose papers and grants you can read here"
      >
        <input v-model="peopleOnly" type="checkbox" />
        Only people in Advisor Atlas
      </label>
      <label>
        <span class="visually-hidden">Funder</span>
        <select v-model="funder">
          <option value="">Every funder</option>
          <option v-for="f in funderOptions" :key="f.funder" :value="f.funder">
            {{ funderName(f.funder) }} ({{ f.grants.toLocaleString() }})
          </option>
        </select>
      </label>
      <label>
        <span class="visually-hidden">Kind of grant</span>
        <select v-model="kind">
          <option value="">Every kind</option>
          <option value="new_lab">New labs (early-career PIs)</option>
          <option value="training">Funds PhD students</option>
        </select>
      </label>
      <label>
        <span class="visually-hidden">Sort grants</span>
        <select v-model="sortBy">
          <option v-if="q" value="">Best match</option>
          <option value="newest">Newest first</option>
          <option value="largest">Largest first</option>
        </select>
      </label>
      <button v-if="narrowed" type="button" class="clear" @click="clearAll">
        Clear
      </button>
    </div>

    <LoadingRows
      v-if="loading && !data"
      label="Loading this university's grants"
      :rows="3"
    />
    <p v-else-if="failed" class="sub">
      Couldn't load the grants. Try again in a moment.
    </p>
    <template v-else-if="data">
      <p v-if="!data.total" class="sub">
        {{
          narrowed
            ? "No grants here match. Try fewer words, or clear the filters."
            : "No grants on record here."
        }}
      </p>
      <template v-else>
        <p :class="{ stale: loading }">
          <strong class="num">{{ data.total.toLocaleString() }}</strong>
          {{ summary }}
        </p>
        <div v-if="totalUSD > 0" class="glance" :class="{ stale: loading }">
          <dl class="stats">
            <div>
              <dt>Awarded, in all</dt>
              <dd>≈ {{ formatMoney(totalUSD, "USD") }}</dd>
            </div>
            <div v-if="runningUSD > 0">
              <dt>In grants running now</dt>
              <dd>≈ {{ formatMoney(runningUSD, "USD") }}</dd>
            </div>
            <div v-if="!onlyRunning">
              <dt>Running now</dt>
              <dd>
                {{ data.active.toLocaleString() }}
                <span class="of">of {{ data.total.toLocaleString() }}</span>
              </dd>
            </div>
          </dl>

          <template v-if="funderBars.length > 1">
            <p class="cap">Money by funder</p>
            <ul class="fbars">
              <li v-for="f in funderBars" :key="f.funder">
                <span class="fname">{{ funderName(f.funder) }}</span>
                <span class="track"
                  ><span class="fill" :style="{ width: f.width + '%' }"></span
                ></span>
                <span class="fval">{{ formatMoney(f.usd, "USD") }}</span>
              </li>
            </ul>
          </template>

          <template v-if="trend.length">
            <p class="cap">
              Grants started per year<template v-if="trendLeftOut">
                (NIH not counted: only its running projects are
                loaded)</template
              >
            </p>
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
          </template>
        </div>

        <p v-if="!peopleOnly" class="legend">
          A name in bold has a profile in Advisor Atlas: open it for their
          papers and grants. Other leads aren't listed here (outside computer
          science, only the most-cited researchers in each field are).
        </p>
        <ul class="grants" :class="{ stale: loading }">
          <li v-for="g in grants" :key="g.funder + g.id">
            <button
              type="button"
              class="link title"
              title="Read the grant: what it funds, who is on it"
              @click="showGrant(g.funder, g.id)"
            >
              {{ grantTitle(g.title) }}
            </button>
            <p class="meta">
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
              ><template v-if="grantYears(g)">, {{ grantYears(g) }}</template>
            </p>
            <p v-if="g.lead" class="meta">
              Led by
              <button
                v-if="g.profile"
                type="button"
                class="link"
                @click="emit('openPerson', g.profile)"
              >
                {{ short(g.profile) }}</button
              ><span v-if="g.profile" class="in-atlas">in Advisor Atlas</span
              ><template v-else>{{ personName(g.lead) }}</template>
            </p>
          </li>
        </ul>
        <button
          v-if="data.grants.length > shown"
          type="button"
          class="show-more"
          @click="shown += 10"
        >
          Show 10 more
        </button>
        <p v-else-if="data.total > data.grants.length" class="sub">
          The {{ data.grants.length }} newest of
          {{ data.total.toLocaleString() }}
          are listed.
        </p>
      </template>
    </template>
  </div>
</template>

<style scoped>
.held {
  margin-top: 16px;
}
.sub {
  color: var(--ink-soft);
  font-size: var(--t-sm);
}
.num {
  font-variant-numeric: tabular-nums;
}
.grants {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
}
.grants li {
  padding: 8px 0;
  border-top: 1px solid var(--rule);
}
.title {
  color: var(--ink);
}
.meta {
  margin: 2px 0 0;
  color: var(--ink-soft);
  font-size: var(--t-sm);
}
.kind,
.lang {
  display: inline-block;
  margin-right: 6px;
  padding: 0 6px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-pill);
  font-size: var(--t-xs);
}
.stale {
  opacity: 0.55;
}
.legend {
  margin: 0 0 4px;
  font-size: var(--t-xs);
  color: var(--ink-faint);
}
.in-atlas {
  display: inline-block;
  margin-left: 6px;
  padding: 0 7px;
  border-radius: var(--radius-pill);
  background: #eef0f3;
  color: var(--ink-soft);
  font-size: 0.72rem;
  font-weight: 600;
  vertical-align: 1px;
}
.glance {
  margin: 10px 0 14px;
  padding: 12px 14px;
  border: 1px solid var(--rule);
  border-radius: var(--radius-box);
  background: var(--surface);
}
.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  margin: 0;
}
.stats dt {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.stats dd {
  margin: 2px 0 0;
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.stats .of {
  font-size: var(--t-xs);
  font-weight: 400;
  color: var(--ink-soft);
}
.cap {
  margin: 14px 0 6px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.fbars {
  list-style: none;
  margin: 0;
  padding: 0;
}
.fbars li {
  display: grid;
  grid-template-columns:
    minmax(0, 9em)
    1fr 4.6em; /* a fixed value column, so the tracks line up */
  gap: 10px;
  align-items: center;
  padding: 3px 0;
  font-size: var(--t-xs);
}
.fname {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}
.track {
  height: 8px;
  background: var(--rule);
  border-radius: 999px;
  overflow: hidden;
}
.fill {
  display: block;
  height: 100%;
  background: var(--line-ai);
}
.fval {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.trend {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 56px;
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
  margin: 4px 0 0;
  font-size: var(--t-xs);
  color: var(--ink-faint);
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
</style>
