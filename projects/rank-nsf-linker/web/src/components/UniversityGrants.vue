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
  grantYears,
  KIND_LABEL,
  short,
  titleLanguage,
  webUrl,
} from "@/lines";
import { funderName } from "@/store";

const props = defineProps<{ universityId: string; goal: string }>();
const emit = defineEmits<{ openPerson: [name: string] }>();

const data = ref<Landscape | null>(null);
const loading = ref(false);
const failed = ref(false);
const onlyRunning = ref(false);
const shown = ref(10);
const q = ref(props.goal); // this tab's search
const funder = ref("");
const kind = ref<"" | "new_lab" | "training">("");
const sortBy = ref<"" | "newest" | "largest">("newest"); // "": best match (with a search)
// Funders to choose from: those of the list before a funder was chosen
const funderOptions = ref<Landscape["funders"]>([]);
const narrowed = computed(
  () => !!q.value || onlyRunning.value || !!funder.value || !!kind.value,
);
function clearAll() {
  q.value = "";
  onlyRunning.value = false;
  funder.value = "";
  kind.value = "";
}
// Another university or a new search on the page: start over from it
watch(
  () => [props.universityId, props.goal],
  () => {
    q.value = props.goal;
    onlyRunning.value = false;
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
        <ul class="grants" :class="{ stale: loading }">
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
              ><template v-else>{{ g.lead }}</template>
            </p>
          </li>
        </ul>
        <button
          v-if="data.grants.length > shown"
          type="button"
          class="link more"
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
