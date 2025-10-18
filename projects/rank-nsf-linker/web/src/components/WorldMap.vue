<template>
  <div class="app">
    <div ref="mapContainer" id="map" class="map-container" />

    <!-- Enhanced Controls Panel -->
    <div class="controls-panel">
      <div class="search-section">
        <input
          v-model="search"
          @input="onSearchInput"
          @keydown.enter.prevent="searchAndFly"
          placeholder="Search university (press Enter)"
          class="search"
        />
      </div>

      <!-- Filters -->
      <div class="filters-section">
        <button class="filter-toggle" @click="showFilters = !showFilters">
          {{ showFilters ? "▼" : "▶" }} Filters & Legend
        </button>

        <div v-if="showFilters" class="filters-content">
          <!-- Research Area Filter -->
          <div class="filter-group">
            <label>Research Areas:</label>
            <div class="area-chips">
              <button
                v-for="(color, area) in AREA_COLORS"
                :key="area"
                @click="toggleAreaFilter(area)"
                :class="['area-chip', { active: activeAreas.has(area) }]"
                :style="{
                  borderColor: color,
                  backgroundColor: activeAreas.has(area)
                    ? color
                    : 'transparent',
                  color: activeAreas.has(area) ? '#fff' : color,
                }"
              >
                {{ area }}
              </button>
            </div>
          </div>

          <!-- Funding Range Filter -->
          <div class="filter-group">
            <label>Funding Range (millions):</label>
            <div class="range-inputs">
              <input
                v-model.number="fundingMin"
                type="number"
                placeholder="Min"
                class="range-input"
              />
              <span>—</span>
              <input
                v-model.number="fundingMax"
                type="number"
                placeholder="Max"
                class="range-input"
              />
            </div>
          </div>

          <!-- NSF Awards Filter -->
          <div class="filter-group">
            <label>
              <input v-model="showNSFOnly" type="checkbox" />
              NSF Award Recipients Only
            </label>
          </div>

          <!-- Visualization Mode -->
          <div class="filter-group">
            <label>Map Visualization:</label>
            <select v-model="vizMode" class="viz-select">
              <option value="area">By Research Area</option>
              <option value="funding">By Funding Amount</option>
              <option value="faculty">By Faculty Count</option>
              <option value="nsf">By NSF Awards</option>
            </select>
          </div>

          <button @click="resetFilters" class="reset-btn">Reset All</button>
        </div>
      </div>

      <!-- Stats Overview -->
      <div class="stats-overview">
        <div class="stat-item">
          <div class="stat-value">{{ filteredUniversities.length }}</div>
          <div class="stat-label">Universities</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ totalFaculty }}</div>
          <div class="stat-label">Faculty</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${{ totalFundingDisplay }}M</div>
          <div class="stat-label">Total Funding</div>
        </div>
      </div>
    </div>

    <!-- Enhanced Side Panel -->
    <aside class="side-panel" v-if="selectedUniversity">
      <button class="close" @click="closePanel">×</button>

      <div v-if="detailLoading" class="loading">Loading details...</div>

      <template v-else>
        <!-- University Header -->
        <div class="uni-header">
          <h2>{{ selectedUniversity.name }}</h2>
          <div class="uni-meta">
            <span
              class="meta-badge"
              :style="{
                backgroundColor: getAreaColor(selectedUniversity.top_area),
              }"
            >
              {{ selectedUniversity.top_area }}
            </span>
            <span v-if="selectedUniversity.ranking" class="meta-badge ranking">
              #{{ selectedUniversity.ranking }}
            </span>
          </div>
        </div>

        <!-- Quick Stats Grid -->
        <div class="quick-stats">
          <div class="stat-card">
            <div class="stat-icon">📍</div>
            <div class="stat-details">
              <div class="stat-label">Location</div>
              <div class="stat-value">
                {{ selectedUniversity.city }}, {{ selectedUniversity.country }}
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-details">
              <div class="stat-label">Research Funding</div>
              <div class="stat-value">
                ${{ (selectedUniversity.funding || 0).toFixed(1) }}M
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <div class="stat-details">
              <div class="stat-label">NSF Awards</div>
              <div class="stat-value">
                {{ selectedUniversity.nsf_awards || 0 }}
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-details">
              <div class="stat-label">Faculty</div>
              <div class="stat-value">
                {{ selectedUniversity.faculty_count || 0 }}
              </div>
            </div>
          </div>

          <div class="stat-card" v-if="selectedUniversity.students">
            <div class="stat-icon">🎓</div>
            <div class="stat-details">
              <div class="stat-label">Students</div>
              <div class="stat-value">
                {{ formatNumber(selectedUniversity.students) }}
              </div>
            </div>
          </div>

          <div class="stat-card" v-if="selectedUniversity.founded">
            <div class="stat-icon">📅</div>
            <div class="stat-details">
              <div class="stat-label">Founded</div>
              <div class="stat-value">{{ selectedUniversity.founded }}</div>
            </div>
          </div>
        </div>

        <div class="uni-links">
          <a
            v-if="selectedUniversity.website"
            :href="selectedUniversity.website"
            target="_blank"
            class="link-btn"
          >
            🔗 Website
          </a>
        </div>

        <hr />

        <!-- Research Areas Distribution -->
        <div v-if="areaDistribution.length" class="section">
          <h3>Research Focus Distribution</h3>
          <div class="area-bars">
            <div
              v-for="area in areaDistribution"
              :key="area.name"
              class="area-bar-item"
            >
              <div class="area-bar-label">
                <span>{{ area.name }}</span>
                <span class="area-bar-count">{{ area.count }}</span>
              </div>
              <div class="area-bar-track">
                <div
                  class="area-bar-fill"
                  :style="{
                    width: area.percentage + '%',
                    backgroundColor: getAreaColor(area.name),
                  }"
                />
              </div>
            </div>
          </div>
        </div>

        <hr />

        <!-- Faculty Section with Sorting and Filtering -->
        <div class="section">
          <div class="section-header">
            <h3>Faculty ({{ filteredFaculty.length }})</h3>
            <div class="faculty-controls">
              <select v-model="facultySort" class="faculty-sort">
                <option value="name">Sort by Name</option>
                <option value="citations">Sort by Citations</option>
                <option value="publications">Sort by Publications</option>
                <option value="hindex">Sort by H-Index</option>
              </select>
            </div>
          </div>

          <!-- Area Filter for Faculty -->
          <div class="faculty-area-filter">
            <button
              v-for="area in uniqueFacultyAreas"
              :key="area"
              @click="toggleFacultyAreaFilter(area)"
              :class="[
                'area-filter-chip',
                { active: activeFacultyAreas.has(area) },
              ]"
              :style="{
                borderColor: getAreaColor(area),
                backgroundColor: activeFacultyAreas.has(area)
                  ? getAreaColor(area)
                  : 'transparent',
                color: activeFacultyAreas.has(area)
                  ? '#fff'
                  : getAreaColor(area),
              }"
            >
              {{ area }}
            </button>
          </div>

          <ul class="faculty-list">
            <li v-for="f in visibleFaculty" :key="f.name" class="fac-row">
              <div class="fac-content">
                <div class="fac-header">
                  <a
                    v-if="f.homepage"
                    :href="f.homepage"
                    target="_blank"
                    class="fac-name-link"
                  >
                    {{ f.name }}
                  </a>
                  <span v-else class="fac-name">{{ f.name }}</span>
                </div>

                <div v-if="f.dept" class="fac-dept">{{ f.dept }}</div>

                <div
                  v-if="f.matched_areas && f.matched_areas.length"
                  class="fac-areas"
                >
                  <span
                    v-for="area in f.matched_areas"
                    :key="area"
                    class="area-tag"
                    :style="{ backgroundColor: getAreaColor(area) }"
                  >
                    {{ area }}
                  </span>
                </div>

                <!-- Faculty Metrics -->
                <div
                  v-if="f.citations || f.publications || f.hindex"
                  class="fac-metrics"
                >
                  <span v-if="f.citations" class="metric"
                    >📊 {{ formatNumber(f.citations) }} citations</span
                  >
                  <span v-if="f.publications" class="metric"
                    >📄 {{ f.publications }} pubs</span
                  >
                  <span v-if="f.hindex" class="metric"
                    >📈 h-index: {{ f.hindex }}</span
                  >
                </div>

                <!-- Research Interests -->
                <div
                  v-if="f.interests && f.interests.length"
                  class="fac-interests"
                >
                  <em>{{ f.interests.join(", ") }}</em>
                </div>
              </div>
            </li>
          </ul>

          <button
            v-if="hasMoreFaculty"
            @click="showMoreFaculty"
            class="more-btn"
          >
            Show
            {{ Math.min(FAC_SLAB, filteredFaculty.length - visibleCount) }} more
          </button>
        </div>

        <!-- Recent NSF Awards Section -->
        <div
          v-if="
            selectedUniversity.recent_nsf_awards &&
            selectedUniversity.recent_nsf_awards.length
          "
          class="section"
        >
          <hr />
          <h3>
            Recent NSF Awards ({{
              selectedUniversity.recent_nsf_awards.length
            }})
          </h3>
          <ul class="nsf-awards-list">
            <li
              v-for="(award, idx) in selectedUniversity.recent_nsf_awards.slice(
                0,
                5
              )"
              :key="idx"
              class="nsf-award"
            >
              <div class="award-title">{{ award.title }}</div>
              <div class="award-meta">
                <span class="award-amount"
                  >${{ formatNumber(award.amount) }}</span
                >
                <span class="award-year">{{ award.year }}</span>
                <span v-if="award.program" class="award-program">{{
                  award.program
                }}</span>
              </div>
            </li>
          </ul>
        </div>
      </template>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from "vue";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import axios from "axios";
import lodash from "lodash";

// -------------------- Types --------------------
type Faculty = {
  name: string;
  homepage?: string;
  dept?: string;
  matched_areas?: string[];
  interests?: string[];
  citations?: number;
  publications?: number;
  hindex?: number;
};

type NSFAward = {
  title: string;
  amount: number;
  year: number;
  program?: string;
};

type UniSummary = {
  id: string;
  name: string;
  longitude: number;
  latitude: number;
  top_area?: string;
  faculty_count?: number;
  funding?: number;
  nsf_awards?: number;
};

type UniDetail = UniSummary & {
  city?: string;
  country?: string;
  website?: string;
  ranking?: number | null;
  faculty?: Faculty[];
  students?: number;
  founded?: number;
  institution_type?: string;
  recent_nsf_awards?: NSFAward[];
};

// -------------------- Config --------------------
const AREA_COLORS: Record<string, string> = {
  AI: "#10b981",
  Systems: "#3b82f6",
  Theory: "#8b5cf6",
  Interdisciplinary: "#f59e0b",
  Other: "#6b7280",
};

const FAC_SLAB = 25;
const CLUSTER_RADIUS = 60;
const POPUP_MAX_WIDTH = 300;

// -------------------- Refs & state --------------------
const mapContainer = ref<HTMLDivElement | null>(null);
let map: maplibregl.Map | null = null;

const allUniversities = ref<UniSummary[]>([]);
const universitiesById = new Map<string, UniSummary>();
const detailsCache = new Map<string, UniDetail>();

const selectedUniversity = ref<null | UniDetail>(null);
const selectedId = ref<string | null>(null);

const detailLoading = ref(false);
const search = ref("");
const popupRef = ref<maplibregl.Popup | null>(null);

const visibleCount = ref(FAC_SLAB);

// Filter states
const showFilters = ref(false);
const activeAreas = ref(new Set<string>(Object.keys(AREA_COLORS)));
const fundingMin = ref<number | null>(null);
const fundingMax = ref<number | null>(null);
const showNSFOnly = ref(false);
const vizMode = ref<"area" | "funding" | "faculty" | "nsf">("area");

// Faculty filters
const facultySort = ref<"name" | "citations" | "publications" | "hindex">(
  "name"
);
const activeFacultyAreas = ref(new Set<string>());

// -------------------- Computed --------------------
const filteredUniversities = computed(() => {
  return allUniversities.value.filter((u) => {
    // Area filter
    if (!activeAreas.value.has(u.top_area || "Other")) return false;

    // Funding filter
    if (fundingMin.value !== null && (u.funding || 0) < fundingMin.value)
      return false;
    if (fundingMax.value !== null && (u.funding || 0) > fundingMax.value)
      return false;

    // NSF filter
    if (showNSFOnly.value && (!u.nsf_awards || u.nsf_awards === 0))
      return false;

    return true;
  });
});

const totalFaculty = computed(() =>
  filteredUniversities.value.reduce((sum, u) => sum + (u.faculty_count || 0), 0)
);

const totalFundingDisplay = computed(() =>
  filteredUniversities.value
    .reduce((sum, u) => sum + (u.funding || 0), 0)
    .toFixed(1)
);

const filteredFaculty = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];

  let faculty = selectedUniversity.value.faculty;

  // Filter by area if any selected
  if (activeFacultyAreas.value.size > 0) {
    faculty = faculty.filter((f) =>
      f.matched_areas?.some((area) => activeFacultyAreas.value.has(area))
    );
  }

  // Sort
  const sorted = [...faculty];
  switch (facultySort.value) {
    case "citations":
      sorted.sort((a, b) => (b.citations || 0) - (a.citations || 0));
      break;
    case "publications":
      sorted.sort((a, b) => (b.publications || 0) - (a.publications || 0));
      break;
    case "hindex":
      sorted.sort((a, b) => (b.hindex || 0) - (a.hindex || 0));
      break;
    default:
      sorted.sort((a, b) => a.name.localeCompare(b.name));
  }

  return sorted;
});

const visibleFaculty = computed(() =>
  filteredFaculty.value.slice(0, visibleCount.value)
);

const hasMoreFaculty = computed(
  () => filteredFaculty.value.length > visibleCount.value
);

const areaDistribution = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];

  const counts: Record<string, number> = {};
  selectedUniversity.value.faculty.forEach((f) => {
    f.matched_areas?.forEach((area) => {
      counts[area] = (counts[area] || 0) + 1;
    });
  });

  const total = Object.values(counts).reduce((sum, c) => sum + c, 0);

  return Object.entries(counts)
    .map(([name, count]) => ({
      name,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
    }))
    .sort((a, b) => b.count - a.count);
});

const uniqueFacultyAreas = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];
  const areas = new Set<string>();
  selectedUniversity.value.faculty.forEach((f) => {
    f.matched_areas?.forEach((area) => areas.add(area));
  });
  return Array.from(areas).sort();
});

// -------------------- Utilities --------------------
function shortLabel(name: string) {
  if (!name) return "";
  const parts = name.split(/\s+/).slice(0, 3);
  return parts
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 4);
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

function getAreaColor(area?: string): string {
  return AREA_COLORS[area || "Other"] || AREA_COLORS.Other;
}

function buildFeatureCollection(summaries: UniSummary[]) {
  const features = summaries.map((u) => {
    universitiesById.set(u.id, u);
    return {
      type: "Feature" as const,
      properties: {
        id: u.id,
        name: u.name,
        top_area: u.top_area ?? "Other",
        label: shortLabel(u.name),
        faculty_count: u.faculty_count ?? 0,
        funding: u.funding ?? 0,
        nsf_awards: u.nsf_awards ?? 0,
      },
      geometry: { type: "Point" as const, coordinates: [u.longitude, u.latitude] },
    };
  });
  return { type: "FeatureCollection" as const, features };
}

// @ts-expect-error TS6133: temporarily unused
function getMarkerColor(props: any, mode: string): string {
  switch (mode) {
    case "funding":
      const funding = props.funding || 0;
      if (funding > 100) return "#dc2626";
      if (funding > 50) return "#ea580c";
      if (funding > 20) return "#f59e0b";
      if (funding > 10) return "#84cc16";
      return "#6b7280";

    case "faculty":
      const count = props.faculty_count || 0;
      if (count > 100) return "#dc2626";
      if (count > 50) return "#ea580c";
      if (count > 25) return "#f59e0b";
      if (count > 10) return "#84cc16";
      return "#6b7280";

    case "nsf":
      const awards = props.nsf_awards || 0;
      if (awards > 50) return "#dc2626";
      if (awards > 25) return "#ea580c";
      if (awards > 10) return "#f59e0b";
      if (awards > 5) return "#84cc16";
      return "#6b7280";

    default: // area
      return getAreaColor(props.top_area);
  }
}

// @ts-expect-error TS6133: temporarily unused
function getMarkerSize(props: any, mode: string): number {
  switch (mode) {
    case "funding":
      const funding = props.funding || 0;
      return Math.min(6 + Math.sqrt(funding) * 0.5, 20);

    case "faculty":
      const count = props.faculty_count || 0;
      return Math.min(6 + Math.sqrt(count) * 0.8, 20);

    case "nsf":
      const awards = props.nsf_awards || 0;
      return Math.min(6 + awards * 0.3, 20);

    default:
      return 10;
  }
}

// -------------------- Filter Functions --------------------
function toggleAreaFilter(area: string) {
  if (activeAreas.value.has(area)) {
    activeAreas.value.delete(area);
  } else {
    activeAreas.value.add(area);
  }
  activeAreas.value = new Set(activeAreas.value);
  updateMapData();
}

function toggleFacultyAreaFilter(area: string) {
  if (activeFacultyAreas.value.has(area)) {
    activeFacultyAreas.value.delete(area);
  } else {
    activeFacultyAreas.value.add(area);
  }
  activeFacultyAreas.value = new Set(activeFacultyAreas.value);
}

function resetFilters() {
  activeAreas.value = new Set(Object.keys(AREA_COLORS));
  fundingMin.value = null;
  fundingMax.value = null;
  showNSFOnly.value = false;
  vizMode.value = "area";
  activeFacultyAreas.value = new Set();
  updateMapData();
}

function updateMapData() {
  if (!map) return;

  const fc = buildFeatureCollection(filteredUniversities.value);
  const source = map.getSource("unis") as maplibregl.GeoJSONSource;
  if (source) {
    source.setData(fc as any);
  }
}

// -------------------- Core logic --------------------
onMounted(async () => {
  if (!mapContainer.value) return;

  map = new maplibregl.Map({
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
    center: [0, 20],
    zoom: 2,
  });

  map.doubleClickZoom.disable();
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: true }),
    "top-left"
  );
  map.addControl(new maplibregl.FullscreenControl(), "top-left");

  try {
    const { data: summaries } = await axios.get<UniSummary[]>(
      "/api/universities/summary"
    );

    allUniversities.value = summaries;
    const fc = buildFeatureCollection(summaries);

    map.addSource("unis", {
      type: "geojson",
      data: fc,
      cluster: true,
      clusterRadius: CLUSTER_RADIUS,
    });

    // Cluster layers
    map.addLayer({
      id: "clusters",
      type: "circle",
      source: "unis",
      filter: ["has", "point_count"],
      paint: {
        "circle-color": [
          "step",
          ["get", "point_count"],
          "#51bbd6",
          10,
          "#f1f075",
          30,
          "#f28cb1",
        ],
        "circle-radius": ["step", ["get", "point_count"], 18, 10, 26, 30, 36],
        "circle-opacity": 0.95,
      },
    });

    map.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "unis",
      filter: ["has", "point_count"],
      layout: { "text-field": "{point_count_abbreviated}", "text-size": 12 },
      paint: { "text-color": "#000" },
    });

    // Dynamic point colors based on viz mode
    updatePointsLayer();

    // Labels
    map.addLayer({
      id: "point-label",
      type: "symbol",
      source: "unis",
      filter: ["!", ["has", "point_count"]],
      layout: {
        "text-field": ["get", "label"],
        "text-size": 10,
        "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
      },
      paint: { "text-color": "#fff" },
    });

    // Selected highlight
    map.addLayer({
      id: "selected-point",
      type: "circle",
      source: "unis",
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-color": "#ff6b6b",
        "circle-radius": 14,
        "circle-stroke-width": 3,
        "circle-stroke-color": "#fff",
      },
    });

    // Fit bounds
    const coords = fc.features.map((f: any) => f.geometry.coordinates);
    if (coords.length) {
      const lons = coords.map((c: any) => c[0]);
      const lats = coords.map((c: any) => c[1]);
      const minLon = Math.min(...lons),
        maxLon = Math.max(...lons),
        minLat = Math.min(...lats),
        maxLat = Math.max(...lats);
      map.fitBounds(
        [
          [minLon, minLat],
          [maxLon, maxLat],
        ],
        { padding: 40, maxZoom: 7, duration: 800 }
      );
    }

    // Click handlers
    map.on("click", "points", (e) => {
      const feature = e.features?.[0];
      if (!feature) return;
      const coords = (feature.geometry as any).coordinates.slice();
      const props = feature.properties as any;
      const id = props.id as string;
      const summary = universitiesById.get(id);
      if (!summary) return;

      popupRef.value?.remove();
      const html = `
        <div class="map-popup">
          <strong>${summary.name}</strong><br/>
          <small>Faculty: ${props.faculty_count ?? 0}</small><br/>
          <small>Funding: $${(props.funding || 0).toFixed(1)}M</small><br/>
          <small>NSF Awards: ${props.nsf_awards || 0}</small><br/>
          <small style="color: #666;">Double-click for details</small>
        </div>`;

      if (map) {
        popupRef.value = new maplibregl.Popup({
          offset: 14,
          closeButton: true,
          className: "map-popup",
          maxWidth: `${POPUP_MAX_WIDTH}px`,
        })
          .setLngLat(coords as [number, number])
          .setHTML(html)
          .addTo(map);
      }
    });

    map.on("click", "clusters", async (e) => {
      const features = map!.queryRenderedFeatures(e.point, {
        layers: ["clusters"],
      });
      if (!features.length) return;
      const clusterId = features[0].properties.cluster_id;
      const source = map!.getSource("unis") as maplibregl.GeoJSONSource;
      const zoomVal = await source.getClusterExpansionZoom(clusterId);
      map!.easeTo({
        center:
          features[0].geometry.type === "Point"
            ? (features[0].geometry.coordinates as [number, number])
            : [0, 0],
        zoom: zoomVal,
        duration: 500,
      });
    });

    map.on("dblclick", "points", async (e) => {
      e.originalEvent?.preventDefault();
      const feature = e.features?.[0];
      if (!feature) return;
      const id = (feature.properties as any).id as string;

      if (detailsCache.has(id)) {
        selectedUniversity.value = detailsCache.get(id)!;
        visibleCount.value = FAC_SLAB;
        selectedId.value = id;
        activeFacultyAreas.value = new Set();
        updateSelectedFilter(id);
        return;
      }

      detailLoading.value = true;
      selectedUniversity.value = {
        id,
        name: "Loading…",
        longitude: 0,
        latitude: 0,
        top_area: "Other",
        faculty_count: 0,
      } as UniDetail;

      try {
        const { data } = await axios.get<UniDetail>(`/api/universities/${id}`);
        detailsCache.set(id, data);
        selectedUniversity.value = data;
        visibleCount.value = FAC_SLAB;
        selectedId.value = id;
        activeFacultyAreas.value = new Set();
        updateSelectedFilter(id);
      } catch (err) {
        console.error("Failed to load details for", id, err);
        selectedUniversity.value = null;
      } finally {
        detailLoading.value = false;
      }
    });

    ["points", "clusters"].forEach((layer) => {
      map!.on(
        "mouseenter",
        layer,
        () => (map!.getCanvas().style.cursor = "pointer")
      );
      map!.on("mouseleave", layer, () => (map!.getCanvas().style.cursor = ""));
    });
  } catch (err) {
    console.error("Failed to load university summaries:", err);
  }
});

function updatePointsLayer() {
  if (!map || !map.getLayer("points")) return;

  map.removeLayer("points");

  // Create dynamic paint properties based on viz mode
  let circleColor: any;
  let circleRadius: any;

  if (vizMode.value === "area") {
    const matchExpr: any[] = ["match", ["get", "top_area"]];
    Object.entries(AREA_COLORS).forEach(([k, v]) => {
      matchExpr.push(k, v);
    });
    matchExpr.push(AREA_COLORS.Other);
    circleColor = matchExpr;
    circleRadius = 10;
  } else if (vizMode.value === "funding") {
    circleColor = [
      "step",
      ["get", "funding"],
      "#6b7280",
      10,
      "#84cc16",
      20,
      "#f59e0b",
      50,
      "#ea580c",
      100,
      "#dc2626",
    ];
    circleRadius = [
      "interpolate",
      ["linear"],
      ["get", "funding"],
      0,
      6,
      100,
      16,
      200,
      20,
    ];
  } else if (vizMode.value === "faculty") {
    circleColor = [
      "step",
      ["get", "faculty_count"],
      "#6b7280",
      10,
      "#84cc16",
      25,
      "#f59e0b",
      50,
      "#ea580c",
      100,
      "#dc2626",
    ];
    circleRadius = [
      "interpolate",
      ["linear"],
      ["get", "faculty_count"],
      0,
      6,
      100,
      16,
      200,
      20,
    ];
  } else {
    // nsf
    circleColor = [
      "step",
      ["get", "nsf_awards"],
      "#6b7280",
      5,
      "#84cc16",
      10,
      "#f59e0b",
      25,
      "#ea580c",
      50,
      "#dc2626",
    ];
    circleRadius = [
      "interpolate",
      ["linear"],
      ["get", "nsf_awards"],
      0,
      6,
      50,
      16,
      100,
      20,
    ];
  }

  map.addLayer(
    {
      id: "points",
      type: "circle",
      source: "unis",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": circleColor,
        "circle-radius": circleRadius,
        "circle-stroke-width": 1,
        "circle-stroke-color": "#fff",
        "circle-opacity": 0.9,
      },
    },
    "point-label"
  );
}

function updateSelectedFilter(id: string | null) {
  if (!map) return;
  const filter = ["==", ["get", "id"], id ?? ""];
  try {
    map.setFilter("selected-point", filter as any);
  } catch (e) {
    // layer may not be added yet
  }
}

// Search handlers
const onSearchInput = lodash.debounce(() => {}, 300);

function searchAndFly() {
  if (!map) return;
  const q = search.value.trim().toLowerCase();
  if (!q) return;
  for (const [id, u] of universitiesById) {
    if (u.name.toLowerCase().includes(q)) {
      map.easeTo({ center: [u.longitude, u.latitude], zoom: 8, duration: 700 });
      if (!detailsCache.has(id))
        axios
          .get(`/api/universities/${id}`)
          .then((r) => detailsCache.set(id, r.data))
          .catch(() => {});
      return;
    }
  }
  console.warn("No match for", q);
}

function showMoreFaculty() {
  visibleCount.value += FAC_SLAB;
}

function closePanel() {
  selectedUniversity.value = null;
  selectedId.value = null;
  activeFacultyAreas.value = new Set();
  updateSelectedFilter(null);
}

// Watch for viz mode changes
watch(vizMode, () => {
  updatePointsLayer();
});

watch(selectedId, (id) => updateSelectedFilter(id ?? null));

onBeforeUnmount(() => {
  popupRef.value?.remove();
  map?.remove();
});
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.app {
  height: 100vh;
  width: 100vw;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial,
    sans-serif;
  background: #f8fafc;
}

.map-container {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  right: 420px;
}

/* Enhanced Controls Panel */
.controls-panel {
  position: absolute;
  left: 12px;
  top: 12px;
  z-index: 11;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 16px;
  max-width: 340px;
}

.search-section {
  margin-bottom: 12px;
}

.search {
  width: 100%;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  transition: all 0.2s;
}

.search:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filters-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

.filter-toggle {
  width: 100%;
  padding: 8px 12px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  text-align: left;
  transition: background 0.2s;
}

.filter-toggle:hover {
  background: #e2e8f0;
}

.filters-content {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.filter-group {
  margin-bottom: 16px;
}

.filter-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.area-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.area-chip {
  padding: 6px 12px;
  border-radius: 20px;
  border: 2px solid;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.area-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
}

.viz-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

.reset-btn {
  width: 100%;
  padding: 8px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.reset-btn:hover {
  background: #dc2626;
}

.stats-overview {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

/* Enhanced Side Panel */
.side-panel {
  position: absolute;
  right: 0;
  top: 0;
  width: 420px;
  height: 100%;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  padding: 24px;
  overflow: auto;
  z-index: 12;
  box-shadow: -4px 0 6px -1px rgba(0, 0, 0, 0.1);
}

.side-panel::-webkit-scrollbar {
  width: 8px;
}

.side-panel::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.side-panel::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.close {
  float: right;
  font-size: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #64748b;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.loading {
  font-style: italic;
  color: #64748b;
  text-align: center;
  padding: 40px 0;
}

.uni-header {
  margin-bottom: 20px;
}

.uni-header h2 {
  margin: 0 0 8px 0;
  font-size: 22px;
  color: #1e293b;
  line-height: 1.3;
}

.uni-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.meta-badge.ranking {
  background: #6366f1;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.stat-details {
  flex: 1;
  min-width: 0;
}

.stat-card .stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.stat-card .stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uni-links {
  margin-bottom: 20px;
}

.link-btn {
  display: inline-block;
  padding: 8px 16px;
  background: #3b82f6;
  color: #fff;
  text-decoration: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}

.link-btn:hover {
  background: #2563eb;
}

hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 20px 0;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #1e293b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  margin: 0;
}

/* Research Area Distribution */
.area-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.area-bar-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.area-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.area-bar-count {
  color: #94a3b8;
}

.area-bar-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.area-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

/* Faculty Section */
.faculty-controls {
  display: flex;
  gap: 8px;
}

.faculty-sort {
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  background: #fff;
  cursor: pointer;
}

.faculty-area-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.area-filter-chip {
  padding: 4px 10px;
  border-radius: 16px;
  border: 1.5px solid;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.area-filter-chip:hover {
  transform: translateY(-1px);
}

.faculty-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.fac-row {
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.fac-row:last-child {
  border-bottom: none;
}

.fac-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fac-header {
  display: flex;
  align-items: baseline;
}

.fac-name-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.fac-name-link:hover {
  text-decoration: underline;
}

.fac-name {
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

.fac-dept {
  font-size: 12px;
  color: #64748b;
}

.fac-areas {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.area-tag {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.fac-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.fac-interests {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.more-btn {
  width: 100%;
  margin-top: 12px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  transition: all 0.2s;
}

.more-btn:hover {
  background: #f8fafc;
  border-color: #3b82f6;
}

/* NSF Awards */
.nsf-awards-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nsf-award {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 8px;
  border-left: 3px solid #3b82f6;
}

.award-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  line-height: 1.4;
}

.award-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.award-amount {
  font-weight: 700;
  color: #059669;
}

.award-year {
  color: #6366f1;
  font-weight: 600;
}

.award-program {
  background: #e0e7ff;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

/* Map Popup */
.map-popup {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  line-height: 1.5;
  padding: 4px;
}

.map-popup strong {
  color: #1e293b;
  font-size: 14px;
}

.map-popup small {
  font-size: 12px;
  color: #64748b;
  display: block;
  margin-top: 2px;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .map-container {
    right: 360px;
  }

  .side-panel {
    width: 360px;
  }

  .controls-panel {
    max-width: 280px;
  }
}

@media (max-width: 768px) {
  .map-container {
    right: 0;
    bottom: 50%;
  }

  .side-panel {
    width: 100%;
    height: 50%;
    top: auto;
    bottom: 0;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }

  .controls-panel {
    max-width: calc(100vw - 24px);
  }

  .quick-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
