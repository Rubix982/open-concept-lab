<script setup lang="ts">
// Libraries
import { ref } from "vue";

// Utils
import { COUNTRIES } from "@/config/countries";

// Stores
import { selectedCountry } from "@/config/mapSettings";

// Styles
import "@/assets/styles/leftPanel.css";

const isExpanded = ref(false);

function togglePanel() {
  isExpanded.value = !isExpanded.value;
}
</script>

<template>
  <div class="left-panel-container">
    <!-- Panel -->
    <div class="left-panel" :class="{ expanded: isExpanded }">
      <!-- Panel Content -->
      <div class="panel-content">
        <h2>Map Settings</h2>

        <select v-model="selectedCountry" class="minimal-dropdown">
          <option :value="null">-- Select a country --</option>
          <option
            v-for="country in COUNTRIES"
            :key="country.code"
            :value="country.code"
          >
            {{ country.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Toggle Button -->
    <button
      class="panel-toggle"
      :class="{ expanded: isExpanded }"
      @click="togglePanel"
      :aria-label="isExpanded ? 'Collapse panel' : 'Expand panel'"
    >
      <!-- Chevron Icon -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="chevron-icon"
        :class="{ rotated: isExpanded }"
      >
        <polyline points="9 18 15 12 9 6"></polyline>
      </svg>
    </button>
  </div>
</template>
