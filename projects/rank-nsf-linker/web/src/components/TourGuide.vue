<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

// A guided tour: each step may act on the app first (run a search, open a profile), then points at
// one element with a short card. Steps wait for their element, so they work while data loads.
export type TourStep = {
  title: string;
  body: string;
  target?: string; // CSS selector; none = a centred card
  before?: () => void | Promise<void>;
};

const props = defineProps<{ steps: TourStep[] }>();
const emit = defineEmits<{ end: [] }>();

const index = ref(0);
type Box = { left: number; top: number; width: number; height: number };
const rect = ref<Box | null>(null);

// The part of the element on screen: a profile taller than the window is highlighted where it is
// visible, not as a strip along the top edge.
function visible(el: HTMLElement): Box {
  const r = el.getBoundingClientRect();
  const top = Math.max(r.top, 8);
  const bottom = Math.min(r.bottom, window.innerHeight - 8);
  return {
    left: r.left,
    top,
    width: r.width,
    height: Math.max(0, bottom - top),
  };
}
const waiting = ref(false);
const card = ref<HTMLElement | null>(null);
const cardStyle = ref<Record<string, string>>({});
let run = 0;

async function waitFor(
  selector: string,
  ms = 10000,
): Promise<HTMLElement | null> {
  const until = Date.now() + ms;
  while (Date.now() < until) {
    const el = document.querySelector<HTMLElement>(selector);
    if (el && el.getBoundingClientRect().height > 0) return el;
    await new Promise((r) => setTimeout(r, 150));
  }
  return null;
}

async function show(i: number) {
  const mine = ++run;
  const step = props.steps[i];
  waiting.value = true;
  rect.value = null;
  await step.before?.();
  const el = step.target ? await waitFor(step.target) : null;
  if (mine !== run) return; // another step started meanwhile
  if (el) {
    el.scrollIntoView({ block: "nearest", behavior: "smooth" });
    await new Promise((r) => setTimeout(r, 350));
  }
  waiting.value = false;
  place(el);
  await nextTick();
  card.value?.querySelector<HTMLElement>(".next")?.focus();
}

// Beside the element when there is room, else below or above it; centred when there is no element.
function place(el: HTMLElement | null) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const cardW = Math.min(340, w - 32);
  if (!el || w < 700) {
    rect.value = el ? visible(el) : null;
    cardStyle.value = el
      ? { left: "16px", right: "16px", bottom: "16px", width: "auto" }
      : {
          left: `${(w - cardW) / 2}px`,
          top: `${Math.max(16, h / 2 - 120)}px`,
          width: `${cardW}px`,
        };
    return;
  }
  const r = el.getBoundingClientRect();
  rect.value = visible(el);
  const gap = 14;
  let left: number;
  let top = Math.min(Math.max(16, r.top), h - 260);
  if (r.left - cardW - gap > 16) left = r.left - cardW - gap;
  else if (r.right + cardW + gap < w - 16) left = r.right + gap;
  else {
    left = Math.min(Math.max(16, r.left), w - cardW - 16);
    top = r.bottom + gap + 220 < h ? r.bottom + gap : Math.max(16, r.top - 240);
  }
  cardStyle.value = { left: `${left}px`, top: `${top}px`, width: `${cardW}px` };
}

function relayout() {
  const step = props.steps[index.value];
  if (!waiting.value)
    place(
      step.target ? document.querySelector<HTMLElement>(step.target) : null,
    );
}

watch(index, (i) => show(i), { immediate: true });
window.addEventListener("resize", relayout);
window.addEventListener("scroll", relayout, true);
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("end");
  else if (e.key === "ArrowRight") next();
  else if (e.key === "ArrowLeft") back();
}
window.addEventListener("keydown", onKey);
onBeforeUnmount(() => {
  run++;
  window.removeEventListener("resize", relayout);
  window.removeEventListener("scroll", relayout, true);
  window.removeEventListener("keydown", onKey);
});

function next() {
  if (index.value < props.steps.length - 1) index.value++;
  else emit("end");
}
function back() {
  if (index.value > 0) index.value--;
}
</script>

<template>
  <div
    class="tour"
    role="dialog"
    aria-modal="false"
    :aria-label="`Tour, step ${index + 1} of ${steps.length}`"
  >
    <div
      v-if="rect"
      class="spot"
      :style="{
        left: `${rect.left - 6}px`,
        top: `${rect.top - 6}px`,
        width: `${rect.width + 12}px`,
        height: `${rect.height + 12}px`,
      }"
    ></div>
    <div v-else class="shade"></div>
    <div ref="card" class="card" :style="cardStyle" aria-live="polite">
      <p class="count">{{ index + 1 }} of {{ steps.length }}</p>
      <h2>{{ steps[index].title }}</h2>
      <p class="body">{{ waiting ? "One moment…" : steps[index].body }}</p>
      <div class="actions">
        <button type="button" class="skip" @click="emit('end')">
          {{ index === steps.length - 1 ? "Close" : "End tour" }}
        </button>
        <span>
          <button v-if="index > 0" type="button" class="back" @click="back">
            Back
          </button>
          <button type="button" class="next" :disabled="waiting" @click="next">
            {{ index === steps.length - 1 ? "Done" : "Next" }}
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tour {
  position: fixed;
  inset: 0;
  z-index: 50;
  pointer-events: none;
}

.shade {
  position: fixed;
  inset: 0;
  background: rgba(29, 42, 58, 0.45);
}

/* The highlighted element shows through a hole in the shade. */
.spot {
  position: fixed;
  border-radius: 8px;
  box-shadow:
    0 0 0 3px var(--line-ai),
    0 0 0 9999px rgba(29, 42, 58, 0.45);
  transition:
    left 0.25s ease,
    top 0.25s ease,
    width 0.25s ease,
    height 0.25s ease;
}

.card {
  position: fixed;
  pointer-events: auto;
  background: #fff;
  color: var(--ink);
  border-radius: var(--radius-box);
  padding: 16px 18px 14px;
  box-shadow: 0 10px 30px rgba(29, 42, 58, 0.25);
}

.count {
  font-size: var(--t-xs);
  color: var(--ink-faint);
  font-weight: 700;
}

h2 {
  margin-top: 4px;
  font-size: var(--t-md);
  font-weight: 800;
}

.body {
  margin-top: 6px;
  font-size: var(--t-sm);
  line-height: 1.5;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
}

.actions span {
  display: flex;
  gap: 8px;
}

button {
  font: inherit;
  cursor: pointer;
}

.skip {
  border: 0;
  background: none;
  padding: 0;
  font-size: var(--t-xs);
  color: var(--ink-soft);
  text-decoration: underline;
}

.back,
.next {
  border-radius: var(--radius-box);
  padding: 6px 14px 5px;
  font-weight: 700;
  font-size: var(--t-sm);
}

.back {
  border: 1px solid var(--rule-strong);
  background: #fff;
  color: var(--ink);
}

.next {
  border: 0;
  background: var(--ink);
  color: #fff;
}

.next:disabled {
  opacity: 0.5;
  cursor: wait;
}

.next:focus-visible,
.back:focus-visible,
.skip:focus-visible {
  outline: 3px solid var(--line-ai);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .spot {
    transition: none;
  }
}
</style>
