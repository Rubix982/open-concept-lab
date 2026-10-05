<script setup lang="ts">
import { computed } from "vue";
import type { Faculty } from "@/api";
import { LINE_COLOR, formatMoney } from "@/lines";
import { areaIndex, funderName, fundersFor, newLabLabel } from "@/store";

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
      </span>
      <span v-else-if="funding"
        >No active {{ funderName(funding.funder) }} grant ({{
          funding.total
        }}
        past)</span
      >
      <span v-else>No {{ coveredNames }} grants on record</span>
    </p>
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

.funding {
  margin-top: 7px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
</style>
