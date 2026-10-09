<script setup lang="ts">
import { computed, ref } from "vue";
import { api, type Award, type Faculty } from "@/api";
import {
  LINE_COLOR,
  formatMoney,
  grantTitle,
  grantYears,
  webUrl,
} from "@/lines";
import {
  areaIndex,
  funderName,
  fundersFor,
  newLabLabel,
  showGrant,
} from "@/store";

const props = defineProps<{
  person: Faculty;
  showUniversity?: boolean;
  selectedAreas: string[];
}>();
defineEmits<{ open: [name: string] }>();

// Selected areas first, then the professor's strongest; at most three.
const tags = computed(() => {
  const ordered = [
    ...props.person.areas.filter((a) => props.selectedAreas.includes(a)),
    ...props.person.areas.filter((a) => !props.selectedAreas.includes(a)),
  ];
  return ordered.slice(0, 3).map((a) => {
    const info = areaIndex.value.get(a);
    return {
      area: a,
      name: info?.name ?? a,
      color: LINE_COLOR[info?.group ?? ""] ?? "var(--ink-soft)",
    };
  });
});

// The funder with the most active grants (then most grants overall) speaks for the row.
const funding = computed(() => props.person.funding?.[0] ?? null);
const covered = computed(() => fundersFor(props.person.country));
const coveredNames = computed(() => covered.value.map(funderName).join(" or "));

// First top-venue paper within six years: usually building a lab, so often recruiting.
const earlyCareer = computed(
  () =>
    !!props.person.first_year &&
    props.person.first_year >= new Date().getFullYear() - 6,
);

// CSRankings disambiguates namesakes with a number ("Wei Wang 0001"); students don't need it.
const displayName = computed(() => props.person.name.replace(/\s+\d{4}$/, ""));

// The running grants behind the count, on request: each links to the funder's own record
const grantsOpen = ref(false);
const running = ref<Award[] | null>(null);
const grantsFailed = ref(false);
async function toggleGrants() {
  grantsOpen.value = !grantsOpen.value;
  if (!grantsOpen.value || running.value) return;
  grantsFailed.value = false;
  try {
    const profile = await api.profile(props.person.name);
    running.value = profile.awards
      .filter((a) => a.active)
      .sort((a, b) => (b.ends ?? "").localeCompare(a.ends ?? ""));
  } catch {
    grantsFailed.value = true;
  }
}
// Roles as funders write them: "CoI", "Co-PI", "Co-Investigator", "PI"
function roleOf(a: Award): string {
  if (a.lead) return "Leads it";
  const r = (a.role ?? "").trim();
  if (/^co-?(pi|principal)/i.test(r)) return "Co-PI"; // "Co-PI", "Co-Principal Investigator"
  if (!r || /^(coi|co-?investigator|pi|principal.*)$/i.test(r))
    return "Co-investigator";
  return r;
}
</script>

<template>
  <li class="row">
    <button type="button" class="hit" @click="$emit('open', person.name)">
      <span class="name">{{ displayName }}</span>
      <span v-if="showUniversity" class="uni">{{ person.university }}</span>
      <span
        v-if="person.source === 'openalex'"
        class="src"
        title="Listed as a researcher here by OpenAlex; not a verified faculty list"
      >
        Researcher (OpenAlex)
      </span>
      <span
        v-if="person.new_lab"
        class="early"
        :title="`${newLabLabel(person.new_lab.funder, person.new_lab.scheme)} until ${(person.new_lab.ends ?? '').slice(0, 4)}: a PI starting out, with money, usually recruiting`"
      >
        New lab, funded
      </span>
      <span
        v-else-if="earlyCareer"
        class="early"
        :title="`First top-venue paper in ${person.first_year}: early-career faculty are often building a lab`"
      >
        Early career
      </span>
    </button>
    <div class="tags">
      <span
        v-for="t in tags"
        :key="t.area"
        class="tag"
        :style="{ '--c': t.color }"
        >{{ t.name }}</span
      >
    </div>
    <p v-if="!person.match && person.latest_work" class="match latest">
      <span class="kind"
        >Latest<template v-if="person.latest_work.year"
          >, {{ person.latest_work.year }}</template
        >:</span
      >
      {{ person.latest_work.title }}
    </p>
    <p v-if="person.match" class="match">
      <span class="kind"
        >{{
          person.match.kind === "paper"
            ? "Paper"
            : `${funderName(person.match.funder ?? "nsf")} grant`
        }}<template v-if="person.match.year">, {{ person.match.year }}</template
        >:</span
      >
      {{ person.match.title }}
    </p>
    <p v-if="funding || covered.length" class="funding">
      <span
        class="fund-dot"
        :class="{ on: (funding?.active ?? 0) > 0 }"
        aria-hidden="true"
      ></span>
      <span v-if="funding && funding.active > 0">
        {{ funding.active }} active {{ funderName(funding.funder) }}
        {{ funding.active === 1 ? "grant" : "grants"
        }}<template
          v-if="(funding.lead_active ?? funding.active) === funding.active"
          >,
          <span class="num">{{
            formatMoney(funding.active_amount, funding.currency)
          }}</span></template
        ><template v-else-if="funding.lead_active"
          >, leads {{ funding.lead_active }} (<span class="num">{{
            formatMoney(funding.active_amount, funding.currency)
          }}</span
          >)</template
        ><template v-else> as co-investigator</template>
        <button
          type="button"
          class="grants-toggle"
          :aria-expanded="grantsOpen"
          @click="toggleGrants"
        >
          {{ grantsOpen ? "Hide" : "Show them" }}
        </button>
      </span>
      <span v-else-if="funding"
        >No active {{ funderName(funding.funder) }} grant ({{
          funding.total
        }}
        past)</span
      >
      <span v-else>No {{ coveredNames }} grants on record</span>
    </p>
    <div v-if="grantsOpen" class="running">
      <p v-if="grantsFailed" class="sub">
        Couldn't load the grants. Open the profile instead.
      </p>
      <p v-else-if="running === null" class="sub">Loading the grants…</p>
      <p v-else-if="!running.length" class="sub">
        No running grants found. Open the profile for their past ones.
      </p>
      <ul v-else>
        <li v-for="a in running" :key="a.funder + a.id">
          <button
            type="button"
            class="link gtitle"
            title="Read the grant: what it funds, who is on it"
            @click="showGrant(a.funder, a.id)"
          >
            {{ grantTitle(a.title) }}
          </button>
          <span class="gmeta">
            {{ roleOf(a) }}, {{ funderName(a.funder)
            }}<template v-if="a.amount"
              >, {{ formatMoney(a.amount, a.currency || "USD") }}</template
            ><template v-if="grantYears(a)">, {{ grantYears(a) }}</template>
          </span>
        </li>
      </ul>
      <p class="sub">
        "Leads" means they are the principal investigator, who usually hires the
        PhD students paid by the grant.
      </p>
    </div>
  </li>
</template>

<style scoped>
.row {
  list-style: none;
  padding: 12px 0 13px;
  border-bottom: 1px solid var(--rule);
}

.hit {
  display: block;
  width: 100%;
  text-align: left;
  border: 0;
  background: none;
  padding: 0;
}

.name {
  display: block;
  font-size: var(--t-md);
  font-weight: 800;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
}

.hit:hover .name {
  text-decoration-color: var(--ink);
}

.src {
  display: inline-block;
  margin-top: 2px;
  font-size: var(--t-xs);
  color: var(--ink-faint);
}

.early {
  display: inline-block;
  margin: 2px 0 0 8px;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--line-systems);
}

.latest {
  color: var(--ink-soft);
}

.uni {
  display: block;
  color: var(--ink-soft);
  font-size: var(--t-xs);
  margin-top: 1px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  margin-top: 6px;
}

.tag {
  font-size: var(--t-xs);
  font-weight: 600;
  color: var(--ink-soft);
  border-left: 3px solid var(--c);
  padding-left: 6px;
  line-height: 1.2;
}

.match {
  margin-top: 7px;
  font-size: var(--t-xs);
  line-height: 1.4;
  color: var(--ink);
}

.kind {
  font-weight: 700;
}

.grants-toggle {
  margin-left: 6px;
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  font-weight: 700;
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
  cursor: pointer;
}
.running {
  margin: 6px 0 2px 15px;
  padding-left: 10px;
  border-left: 2px solid var(--rule);
  font-size: var(--t-xs);
}
.running ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.running li {
  padding: 4px 0;
}
.running a {
  color: var(--ink);
  font-weight: 600;
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
}
.gmeta {
  display: block;
  color: var(--ink-soft);
}
.running .sub {
  margin: 4px 0 0;
  color: var(--ink-faint);
}
.funding {
  margin-top: 7px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
</style>
