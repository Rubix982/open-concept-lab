<script setup lang="ts">
// Something is being fetched: placeholder rows shaped like the list that is coming, with a soft
// shimmer, and one line saying what is happening. `bar` instead draws a thin moving line, for a
// refresh while the previous results stay on screen.
withDefaults(defineProps<{ label?: string; rows?: number; bar?: boolean }>(), {
  label: "Loading",
  rows: 4,
  bar: false,
});
</script>

<template>
  <div v-if="bar" class="bar" role="status" :aria-label="label">
    <span />
  </div>
  <div v-else class="loading" role="status">
    <p class="label">{{ label }}</p>
    <div v-for="i in rows" :key="i" class="row" aria-hidden="true">
      <span class="line title" :style="{ width: `${88 - ((i * 17) % 34)}%` }" />
      <span class="line sub" :style="{ width: `${52 - ((i * 11) % 20)}%` }" />
    </div>
  </div>
</template>

<style scoped>
.loading {
  padding: 4px 0 8px;
}

.label {
  font-size: var(--t-xs);
  color: var(--ink-soft);
  margin-bottom: 10px;
}

.label::before {
  content: "";
  display: inline-block;
  width: 9px;
  height: 9px;
  margin-right: 8px;
  border-radius: 50%;
  border: 2px solid var(--line-ai);
  border-right-color: transparent;
  vertical-align: -1px;
  animation: spin 0.9s linear infinite;
}

.row {
  padding: 11px 0 12px;
  border-bottom: 1px solid var(--rule);
}

.line {
  display: block;
  height: 11px;
  border-radius: 6px;
  background: linear-gradient(90deg, #e9edf1 0%, #f5f7f9 45%, #e9edf1 90%);
  background-size: 300% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.line.title {
  height: 13px;
  margin-bottom: 8px;
}

.bar {
  position: relative;
  height: 3px;
  overflow: hidden;
  background: #e3e8ee;
  border-radius: 2px;
  margin: 0 0 10px;
}

.bar span {
  position: absolute;
  inset: 0 auto 0 0;
  width: 35%;
  background: var(--line-ai);
  border-radius: 2px;
  animation: slide 1.1s ease-in-out infinite;
}

@keyframes shimmer {
  from {
    background-position: 100% 0;
  }
  to {
    background-position: 0 0;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes slide {
  from {
    left: -35%;
  }
  to {
    left: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .line,
  .label::before,
  .bar span {
    animation: none;
  }

  .bar span {
    left: 0;
    width: 100%;
    opacity: 0.5;
  }
}
</style>
