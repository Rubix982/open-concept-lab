<script setup lang="ts">
// The grants held at one university (its page): how many, how many running, by whom. On a search,
// the ones about it. Newest first; the funding search filtered to this university (server/landscape.go).
import { computed, ref, watch } from "vue";
import { api, type Landscape } from "@/api";
import LoadingRows from "@/components/LoadingRows.vue";
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
let inflight: AbortController | null = null;

async function load() {
  inflight?.abort();
  const mine = new AbortController();
  inflight = mine;
  loading.value = true;
  failed.value = false;
  try {
    data.value = await api.landscape(
      {
        goal: props.goal,
        university: props.universityId,
        active: onlyRunning.value,
        sort: "newest",
      },
      mine.signal,
    );
  } catch (e) {
    if ((e as Error).name !== "AbortError") failed.value = true;
  } finally {
    if (inflight === mine) loading.value = false; // only the latest request clears the spinner
  }
}
watch(
  () => [props.universityId, props.goal, onlyRunning.value],
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
    <div class="head">
      <p class="sub">
        {{ goal ? `Grants held here about “${goal}”` : "Grants held here" }}
      </p>
      <label class="toggle">
        <input v-model="onlyRunning" type="checkbox" />
        Running now
      </label>
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
          onlyRunning
            ? "No running grants on record here."
            : goal
              ? "No grants on record here about this search."
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
.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.sub {
  color: var(--ink-soft);
  font-size: var(--t-sm);
}
.toggle {
  font-size: var(--t-sm);
  white-space: nowrap;
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
