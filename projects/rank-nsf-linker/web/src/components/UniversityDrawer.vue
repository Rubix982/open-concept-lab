<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { api, type Faculty, type Query, type UniversityDetail } from "@/api";
import FacultyRow from "./FacultyRow.vue";
import ProfessorView from "./ProfessorView.vue";

const props = defineProps<{ id: string; query: Query; professor: string | null }>();
const emit = defineEmits<{ close: []; openProfessor: [name: string | null] }>();

const uni = ref<UniversityDetail | null>(null);
const faculty = ref<Faculty[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [detail, people] = await Promise.all([
      api.university(props.id),
      api.faculty({ ...props.query, university: props.id, limit: 150 }),
    ]);
    uni.value = detail;
    faculty.value = people;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

watch(() => [props.id, props.query.areas.join(","), props.query.goal], load, { immediate: true });

const hasAreas = computed(() => props.query.areas.length > 0);
const funded = computed(() => faculty.value.filter((f) => f.active_awards > 0).length);
const place = computed(() => [uni.value?.city, uni.value?.state].filter(Boolean).join(", "));
const carnegieLabel = computed(() =>
  uni.value?.carnegie === "R1"
    ? "R1: very high research activity"
    : uni.value?.carnegie === "R2"
      ? "R2: high research activity"
      : "",
);

function money(n?: number) {
  return n ? `$${n.toLocaleString("en-US")}` : "";
}
</script>

<template>
  <aside class="drawer" :aria-label="uni?.name ?? 'University'">
    <button type="button" class="close" aria-label="Close" @click="emit('close')">Close</button>

    <ProfessorView
      v-if="professor"
      :name="professor"
      :back-label="uni?.name ?? 'university'"
      @back="emit('openProfessor', null)"
    />

    <div v-else class="uni">
      <p v-if="error" class="error">{{ error }}</p>
      <template v-if="uni">
        <header>
          <h2>{{ uni.name }}</h2>
          <p class="place">{{ place }}</p>
          <p v-if="carnegieLabel" class="carnegie">{{ carnegieLabel }}</p>
        </header>

        <dl class="facts">
          <div>
            <dt>CS faculty</dt>
            <dd class="num">{{ uni.faculty_total }}</dd>
          </div>
          <div v-if="uni.grad_enrollment">
            <dt>Graduate students</dt>
            <dd class="num">{{ uni.grad_enrollment.toLocaleString("en-US") }}</dd>
          </div>
          <div v-if="uni.grad_tuition_out_of_state">
            <dt>Graduate tuition per year</dt>
            <dd class="num">
              {{ money(uni.grad_tuition_out_of_state) }}
              <span v-if="uni.grad_tuition_in_state && uni.grad_tuition_in_state !== uni.grad_tuition_out_of_state" class="sub">
                {{ money(uni.grad_tuition_in_state) }} in-state
              </span>
            </dd>
          </div>
        </dl>

        <section class="funding">
          <h3>Paying for a PhD here</h3>
          <p>
            <strong class="num">{{ funded }}</strong> of the {{ faculty.length }} faculty
            {{ hasAreas ? "in your areas" : "listed below" }} have an active NSF grant.
            PhD students are usually paid as research or teaching assistants, which also covers tuition, and
            faculty with active grants are the ones hiring research assistants.
          </p>
          <p class="sub">
            US citizens and permanent residents can also apply for the
            <a href="https://www.nsfgrfp.org/" target="_blank" rel="noopener">NSF Graduate Research Fellowship</a>.
          </p>
        </section>

        <section>
          <h3>{{ query.goal ? "Faculty whose work matches your goal" : hasAreas ? "Faculty in your areas" : "Faculty" }}</h3>
          <p v-if="!loading && !faculty.length" class="sub">
            No faculty here match. Try fewer words in your goal, or another area.
          </p>
          <ul class="list">
            <FacultyRow
              v-for="f in faculty"
              :key="f.name"
              :person="f"
              :selected-areas="query.areas"
              @open="emit('openProfessor', $event)"
            />
          </ul>
        </section>

        <a v-if="uni.homepage" class="home" :href="uni.homepage.startsWith('http') ? uni.homepage : `https://${uni.homepage}`" target="_blank" rel="noopener">
          University website
        </a>
      </template>
    </div>
  </aside>
</template>

<style scoped>
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
