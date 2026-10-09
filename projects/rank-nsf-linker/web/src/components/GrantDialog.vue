<script setup lang="ts">
// A grant in full, inside Advisor Atlas: what it funds, who is on it, where, how much and until when.
// Funders' own pages can be out of reach (NSF's award pages are blocked from Pakistan), so the
// funder's record is the second step here, not the only one.
import { computed, onMounted, ref, watch } from "vue";
import { api, type GrantDetail } from "@/api";
import LoadingRows from "@/components/LoadingRows.vue";
import {
  approxUSD,
  formatMoney,
  formatYear,
  grantTitle,
  KIND_LABEL,
  niceName,
  personName,
  short,
  webUrl,
} from "@/lines";
import { funderName, shownGrant } from "@/store";

const emit = defineEmits<{
  openPerson: [name: string];
  openUniversity: [id: string];
}>();

const dialog = ref<HTMLDialogElement | null>(null);
const grant = ref<GrantDetail | null>(null);
const failed = ref("");

async function load() {
  const g = shownGrant.value;
  if (!g) return;
  grant.value = null;
  failed.value = "";
  try {
    grant.value = await api.grant(g.funder, g.id);
  } catch (e) {
    failed.value = (e as Error).message;
  }
}
onMounted(() => {
  dialog.value?.showModal();
  load();
});
watch(shownGrant, load);

function close() {
  shownGrant.value = null;
}
// Paragraphs: a blank line starts one. NIH wraps its text at a fixed width ("osteoarthritis and\n
// sometimes"), so a single line break is a space, and a word split across lines ("life-\nchanging")
// is joined. Boilerplate headings ("Project Abstract/Summary") are dropped.
const HEADING =
  /^(project\s+)?(abstract|summary|narrative|description)(\s*\/\s*(abstract|summary))?\s*[:.-]?\s*$/i;
const paragraphs = computed(() =>
  (grant.value?.abstract ?? "")
    .replace(/\r/g, "")
    .split(/\n\s*\n/)
    .map((p) => {
      const lines = p.split("\n").map((l) => l.trim());
      while (lines.length && (!lines[0] || HEADING.test(lines[0])))
        lines.shift(); // a heading line on its own
      return lines
        .join("\n")
        .replace(/(\p{L})-\n(\p{Ll})/gu, "$1-$2")
        .replace(/\s*\n\s*/g, " ")
        .replace(/^(project\s+)?(abstract|summary)\s*:\s*/i, "") // "Abstract: The ..."
        .trim();
    })
    .filter(Boolean),
);
const years = computed(() => {
  const g = grant.value;
  if (!g) return "";
  const from = formatYear(g.starts);
  const to = formatYear(g.ends);
  return [from, to].filter(Boolean).join("–");
});
function goPerson(name: string) {
  close();
  emit("openPerson", name);
}
function goUniversity(id: string) {
  close();
  emit("openUniversity", id);
}
</script>

<template>
  <dialog
    ref="dialog"
    class="grant"
    aria-labelledby="grant-title"
    @close="close"
    @click.self="dialog?.close()"
  >
    <LoadingRows v-if="!grant && !failed" label="Loading the grant" :rows="4" />
    <p v-else-if="failed" class="error">
      {{
        /not found/i.test(failed)
          ? "This grant isn't in Advisor Atlas's data any more."
          : failed
      }}
    </p>
    <template v-else-if="grant">
      <p class="eyebrow">
        {{ funderName(grant.funder) }} grant
        <span v-if="grant.active" class="state on">Running</span>
        <span v-else class="state">Ended</span>
        <span v-if="grant.signal" class="kind" :class="grant.signal">{{
          KIND_LABEL[grant.signal]
        }}</span>
      </p>
      <h2 id="grant-title">{{ grantTitle(grant.title) }}</h2>

      <dl class="facts">
        <div v-if="grant.amount">
          <dt>Amount</dt>
          <dd>
            {{ formatMoney(grant.amount, grant.currency ?? "USD") }}
            <span
              v-if="approxUSD(grant.amount_usd, grant.currency)"
              class="sub"
            >
              {{ approxUSD(grant.amount_usd, grant.currency) }}</span
            >
          </dd>
        </div>
        <div v-if="years">
          <dt>Years</dt>
          <dd>{{ years }}</dd>
        </div>
        <div v-if="grant.institution">
          <dt>Held at</dt>
          <dd>
            <button
              v-if="grant.university_id"
              type="button"
              class="link"
              @click="goUniversity(grant.university_id)"
            >
              {{ niceName(grant.institution) }}
            </button>
            <template v-else>{{ niceName(grant.institution) }}</template>
          </dd>
        </div>
        <div v-if="grant.programs.length">
          <dt>{{ grant.funder === "nsf" ? "Programme" : "Scheme" }}</dt>
          <dd>{{ grant.programs.join(", ") }}</dd>
        </div>
      </dl>

      <section v-if="grant.team.length">
        <h3>Who is on it</h3>
        <ul class="team">
          <li v-for="m in grant.team" :key="m.name + (m.role ?? '')">
            <button
              v-if="m.profile"
              type="button"
              class="link"
              @click="goPerson(m.profile)"
            >
              {{ short(m.profile) }}
            </button>
            <template v-else>{{ personName(m.name) }}</template>
            <span class="role">{{
              m.role === "PI" ? "leads it" : (m.role ?? "")
            }}</span>
            <span v-if="m.profile" class="in-atlas">in Advisor Atlas</span>
          </li>
        </ul>
        <p class="sub">
          The one who leads it usually hires the PhD students a grant pays for.
        </p>
      </section>

      <section>
        <h3>What it funds</h3>
        <p v-if="!paragraphs.length" class="sub">
          {{ funderName(grant.funder) }} publishes no summary for this grant.
        </p>
        <p v-for="(p, i) in paragraphs" :key="i" class="abstract">{{ p }}</p>
      </section>

      <div class="actions">
        <a
          v-if="webUrl(grant.url)"
          :href="webUrl(grant.url)"
          target="_blank"
          rel="noopener"
          class="official"
          >The record at {{ funderName(grant.funder) }}</a
        >
        <form method="dialog"><button class="close">Close</button></form>
      </div>
      <p v-if="webUrl(grant.url)" class="sub note">
        The funder's site can be unavailable in some countries ({{
          grant.funder === "nsf" ? "NSF's is, from Pakistan" : "check yours"
        }}); everything above is the same record.
      </p>
    </template>
    <form v-if="!grant" method="dialog">
      <button class="close">Close</button>
    </form>
  </dialog>
</template>

<style scoped>
.grant {
  width: min(720px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  border: 0;
  border-radius: var(--radius-box);
  padding: 22px 26px;
  color: var(--ink);
}
.grant::backdrop {
  background: rgba(29, 42, 58, 0.45);
}
.eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 0 0 6px;
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink-soft);
}
.state,
.kind,
.in-atlas {
  display: inline-block;
  padding: 0 7px;
  border-radius: var(--radius-pill);
  background: #eef0f3;
  color: var(--ink-soft);
  font-size: 0.72rem;
  font-weight: 700;
}
.state.on {
  background: var(--ink);
  color: #fff;
}
.kind.new_lab {
  background: #e3f1e6;
}
.kind.training {
  background: #fdf0d8;
}
h2 {
  margin: 0 0 14px;
  font-size: var(--t-lg);
  font-weight: 800;
  line-height: 1.25;
}
h3 {
  margin: 18px 0 8px;
  padding-bottom: 5px;
  border-bottom: 2px solid var(--ink);
  font-size: var(--t-sm);
  font-weight: 800;
}
.facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px 20px;
  margin: 0;
}
.facts dt {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.facts dd {
  margin: 2px 0 0;
  font-weight: 700;
}
.team {
  list-style: none;
  margin: 0;
  padding: 0;
}
.team li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
  padding: 3px 0;
}
.role {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.abstract {
  margin: 0 0 10px;
  max-width: 68ch;
  line-height: 1.55;
}
.sub {
  font-size: var(--t-xs);
  color: var(--ink-soft);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
}
.official {
  font-size: var(--t-xs);
  font-weight: 700;
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
}
.note {
  margin: 6px 0 0;
}
.close {
  border: 0;
  border-radius: var(--radius-box);
  background: var(--ink);
  color: #fff;
  font: inherit;
  font-weight: 700;
  padding: 7px 16px 6px;
  cursor: pointer;
}
.error {
  color: var(--danger);
}
</style>
