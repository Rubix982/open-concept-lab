<script setup lang="ts">
// A search box for one tab's list: the search runs on Enter or the button (each runs a server
// search), or, with live, as you type (a list already loaded); × clears it.
import { ref, useId, watch } from "vue";

const props = defineProps<{
  modelValue: string;
  placeholder: string;
  label: string;
  live?: boolean;
}>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const inputId = useId();
const text = ref(props.modelValue);
watch(
  () => props.modelValue,
  (v) => (text.value = v),
);
watch(text, (v) => {
  if (props.live) emit("update:modelValue", v.trim());
});
function submit() {
  emit("update:modelValue", text.value.trim());
}
function clear() {
  text.value = "";
  emit("update:modelValue", "");
}
</script>

<template>
  <form class="tab-search" role="search" @submit.prevent="submit">
    <label class="visually-hidden" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      v-model="text"
      type="search"
      :placeholder="placeholder"
      autocomplete="off"
    />
    <button
      v-if="modelValue"
      type="button"
      class="x"
      aria-label="Clear the search"
      @click="clear"
    >
      ×
    </button>
    <button v-if="!live" type="submit" class="go">Search</button>
  </form>
</template>

<style scoped>
.tab-search {
  display: flex;
  align-items: stretch;
  margin-top: 14px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-box);
  background: var(--surface);
  overflow: hidden;
}
.tab-search:focus-within {
  border-color: var(--ink);
}
input {
  flex: 1;
  min-width: 0;
  border: 0;
  padding: 7px 10px;
  font: inherit;
  font-size: var(--t-sm);
  background: transparent;
  color: var(--ink);
}
input:focus {
  outline: none;
}
input::-webkit-search-cancel-button {
  display: none;
}
.x {
  border: 0;
  background: none;
  padding: 0 8px;
  font-size: 18px;
  color: var(--ink-soft);
  cursor: pointer;
}
.go {
  border: 0;
  border-left: 1px solid var(--rule-strong);
  background: var(--ink);
  color: #fff;
  padding: 0 12px;
  font: inherit;
  font-size: var(--t-xs);
  font-weight: 700;
  cursor: pointer;
}
.go:focus-visible,
.x:focus-visible {
  outline: 2px solid var(--ink);
  outline-offset: -2px;
}
</style>
