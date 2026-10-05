<script setup lang="ts">
import { ref } from "vue";
import { api, type Faculty } from "@/api";
import { removeSaved, savedPeople, savedUniversities } from "@/shortlist";
import { funderName, fundersFor, newLabLabel } from "@/store";
import { countryName } from "@/countries";

// The student's saved professors side by side, and their saved universities. Facts are loaded when
// the list opens, so they are current.
const emit = defineEmits<{
  openPerson: [name: string, universityId: string | null];
  openUniversity: [id: string];
}>();

type Row = { name: string; person: Faculty | null };
const rows = ref<Row[]>([]);
const dialog = ref<HTMLDialogElement | null>(null);

async function open() {
  dialog.value?.showModal();
  rows.value = savedPeople.value.map((s) => ({
    name: s.id,
    person: null,
  }));
  await Promise.all(
    rows.value.map(async (r, i) => {
      try {
        const p = await api.profile(r.name);
        rows.value[i] = { name: r.name, person: p.faculty };
      } catch {
        // gone from the data since it was saved: the row keeps its name
      }
    }),
  );
}
defineExpose({ open, close: () => dialog.value?.close() });

const thisYear = new Date().getFullYear();
// From the precomputed funding summary (as on faculty rows), so it reads the same everywhere.
function funding(r: Row): string {
  const p = r.person;
  if (!p) return "";
  const running = (p.funding ?? []).filter((f) => f.active > 0);
  if (!running.length) {
    return fundersFor(p.country).length
      ? "None running on record"
      : `No grant data for ${countryName(p.country)}`;
  }
  const n = running.reduce((a, f) => a + f.active, 0);
  const lead = running.reduce((a, f) => a + (f.lead_active ?? 0), 0);
  return `${n} running (${running.map((f) => funderName(f.funder)).join(", ")})${lead ? `, leads ${lead}` : ""}`;
}
function stage(p: Faculty | null): string {
  if (!p) return "";
  if (p.new_lab)
    return `New lab: ${newLabLabel(p.new_lab.funder, p.new_lab.scheme)}`;
  if (p.first_year && p.first_year >= thisYear - 6)
    return `Early career (first paper ${p.first_year})`;
  return p.first_year ? `Publishing since ${p.first_year}` : "";
}
function goTo(fn: () => void) {
  dialog.value?.close();
  fn();
}
</script>

<template>
  <dialog ref="dialog" class="shortlist" aria-labelledby="shortlist-title">
    <h2 id="shortlist-title">Your list</h2>
    <p v-if="!savedPeople.length && !savedUniversities.length" class="empty">
      Nothing saved yet. Open a professor or a university and choose “Save to
      your list”. The list stays in this browser.
    </p>

    <section v-if="savedPeople.length">
      <h3>Professors</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Stage</th>
              <th scope="col">Grants</th>
              <th scope="col">Newest paper</th>
              <th scope="col"><span class="visually-hidden">Remove</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.name">
              <th scope="row">
                <button
                  type="button"
                  class="link"
                  @click="
                    goTo(() =>
                      emit(
                        'openPerson',
                        r.name,
                        r.person?.university_id ?? null,
                      ),
                    )
                  "
                >
                  {{ r.name.replace(/\s+\d{4}$/, "") }}
                </button>
                <span class="sub">{{ r.person?.university }}</span>
              </th>
              <td>{{ stage(r.person) }}</td>
              <td>{{ r.person ? funding(r) : "" }}</td>
              <td>
                <template v-if="r.person?.latest_work">
                  {{ r.person.latest_work.year }}:
                  {{ r.person.latest_work.title }}
                </template>
              </td>
              <td>
                <button
                  type="button"
                  class="remove"
                  :aria-label="`Remove ${r.name}`"
                  @click="
                    removeSaved('person', r.name);
                    rows = rows.filter((x) => x.name !== r.name);
                  "
                >
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="savedUniversities.length">
      <h3>Universities</h3>
      <ul class="unis">
        <li v-for="u in savedUniversities" :key="u.id">
          <button
            type="button"
            class="link"
            @click="goTo(() => emit('openUniversity', u.id))"
          >
            {{ u.label }}
          </button>
          <span class="sub">{{ u.sub }}</span>
          <button
            type="button"
            class="remove"
            :aria-label="`Remove ${u.label}`"
            @click="removeSaved('university', u.id)"
          >
            Remove
          </button>
        </li>
      </ul>
    </section>

    <form method="dialog"><button class="close">Close</button></form>
  </dialog>
</template>

<style scoped>
.shortlist {
  width: min(880px, calc(100vw - 32px));
  border: 0;
  border-radius: var(--radius-box);
  padding: 24px 26px;
  color: var(--ink);
}

.shortlist::backdrop {
  background: rgba(29, 42, 58, 0.45);
}

h2 {
  font-size: var(--t-lg);
  font-weight: 800;
  margin-bottom: 12px;
}

h3 {
  font-size: var(--t-sm);
  font-weight: 800;
  margin: 16px 0 8px;
  padding-bottom: 5px;
  border-bottom: 2px solid var(--ink);
}

.empty {
  color: var(--ink-soft);
  line-height: 1.5;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--t-xs);
  line-height: 1.45;
}

th,
td {
  text-align: left;
  vertical-align: top;
  padding: 8px 10px 8px 0;
  border-bottom: 1px solid var(--rule);
}

thead th {
  color: var(--ink-faint);
  font-weight: 700;
}

tbody th {
  min-width: 160px;
}

td:nth-child(4) {
  min-width: 220px;
}

.sub {
  display: block;
  font-size: var(--t-xs);
  font-weight: 400;
  color: var(--ink-soft);
}

.unis {
  margin: 0;
  padding: 0;
  list-style: none;
}

.unis li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--rule);
}

.unis .sub {
  display: inline;
}

.unis .remove {
  margin-left: auto;
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

.remove {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  font-size: var(--t-xs);
  color: var(--ink-soft);
  text-decoration: underline;
  cursor: pointer;
}

.close {
  margin-top: 18px;
  border: 0;
  border-radius: var(--radius-box);
  background: var(--ink);
  color: #fff;
  font-weight: 700;
  padding: 7px 16px 6px;
  cursor: pointer;
}
</style>
