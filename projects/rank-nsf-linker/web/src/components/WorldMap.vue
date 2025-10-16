<template>
  <div class="app">
    <div ref="mapContainer" id="map" class="map-container" />

    <div class="controls">
      <input
        v-model="search"
        @input="onSearchInput"
        @keydown.enter.prevent="searchAndFly"
        placeholder="Search university (press Enter)"
        class="search"
      />
    </div>

    <aside class="side-panel" v-if="selectedUniversity">
      <button class="close" @click="closePanel">×</button>

      <div v-if="detailLoading" class="loading">Loading…</div>

      <template v-else>
        <h2>{{ selectedUniversity.name }}</h2>
        <p><strong>City:</strong> {{ selectedUniversity.city ?? "—" }}</p>
        <p><strong>Country:</strong> {{ selectedUniversity.country ?? "—" }}</p>
        <p>
          <strong>Ranking:</strong> {{ selectedUniversity.ranking ?? "N/A" }}
        </p>
        <p>
          <strong>Website:</strong>
          <a :href="selectedUniversity.website" target="_blank">{{
            selectedUniversity.website
          }}</a>
        </p>

        <hr />
        <h3>Faculty ({{ (selectedUniversity.faculty || []).length }})</h3>

        <ul class="faculty-list">
          <li v-for="(f, idx) in visibleFaculty" :key="f.name" class="fac-row">
            <div class="fac-name">
              <a v-if="f.homepage" :href="f.homepage" target="_blank">{{
                f.name
              }}</a>
              <span v-else>{{ f.name }}</span>
              <div class="fac-dept" v-if="f.dept">{{ f.dept }}</div>
              <div class="fac-areas">
                <em>{{ (f.matched_areas || []).join(", ") }}</em>
              </div>
            </div>
          </li>
        </ul>

        <button v-if="hasMoreFaculty" @click="showMoreFaculty" class="more-btn">
          Show more
        </button>
      </template>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from "vue";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import axios from "axios";
import debounce from "lodash.debounce"; // optional: you can remove and implement custom debounce

// -------------------- Types --------------------
type Faculty = {
  name: string;
  homepage?: string;
  dept?: string;
  matched_areas?: string[];
};
type UniSummary = {
  id: string;
  name: string;
  longitude: number;
  latitude: number;
  top_area?: string;
  faculty_count?: number;
};
type UniDetail = UniSummary & {
  city?: string;
  country?: string;
  website?: string;
  ranking?: number | null;
  faculty?: Faculty[];
};

// -------------------- Config --------------------
const AREA_COLORS: Record<string, string> = {
  AI: "#1f8f3a",
  Systems: "#1e6fb6",
  Theory: "#7a4fbf",
  Interdisciplinary: "#d9772b",
  Other: "#6b6b6b",
};

const FAC_SLAB = 25; // show first N faculty; click "Show more" to expand
const CLUSTER_RADIUS = 60; // increase for more aggressive clustering
const POPUP_MAX_WIDTH = 520;

// -------------------- Refs & state --------------------
const mapContainer = ref<HTMLDivElement | null>(null);
let map: maplibregl.Map | null = null;

const universitiesById = new Map<string, UniSummary>(); // summary lookup
const detailsCache = new Map<string, UniDetail>(); // lazy-loaded details cache

const selectedUniversity = ref<null | UniDetail>(null);
const selectedId = ref<string | null>(null);

const detailLoading = ref(false);
const search = ref("");
const popupRef = ref<maplibregl.Popup | null>(null);

const visibleCount = ref(FAC_SLAB);

// computed helpers used in template
const visibleFaculty = computed(
  () => selectedUniversity.value?.faculty?.slice(0, visibleCount.value) ?? []
);
const hasMoreFaculty = computed(
  () => (selectedUniversity.value?.faculty?.length ?? 0) > visibleCount.value
);

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

function buildFeatureCollection(summaries: UniSummary[]) {
  const features = summaries.map((u) => {
    universitiesById.set(u.id, u);
    return {
      type: "Feature",
      properties: {
        id: u.id,
        name: u.name,
        top_area: u.top_area ?? "Other",
        label: shortLabel(u.name),
        faculty_count: u.faculty_count ?? 0,
      },
      geometry: { type: "Point", coordinates: [u.longitude, u.latitude] },
    };
  });
  return { type: "FeatureCollection", features };
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

  // UX choices
  map.doubleClickZoom.disable();
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: true }),
    "top-left"
  );
  map.addControl(new maplibregl.FullscreenControl(), "top-left");

  try {
    // Prefer a lightweight summary endpoint on the server
    const { data: summaries } = await axios.get<UniSummary[]>(
      "/api/universities/summary"
    );

    const fc = buildFeatureCollection(summaries);

    // Add geojson source with clustering
    map.addSource("unis", {
      type: "geojson",
      data: fc,
      cluster: true,
      clusterRadius: CLUSTER_RADIUS,
    });

    // cluster circle
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

    // cluster count label
    map.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "unis",
      filter: ["has", "point_count"],
      layout: { "text-field": "{point_count_abbreviated}", "text-size": 12 },
      paint: { "text-color": "#000" },
    });

    // match expression for area colors
    const matchExpr: any[] = ["match", ["get", "top_area"]];
    Object.entries(AREA_COLORS).forEach(([k, v]) => {
      matchExpr.push(k, v);
    });
    matchExpr.push(AREA_COLORS.Other);

    // unclustered points
    map.addLayer({
      id: "points",
      type: "circle",
      source: "unis",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": matchExpr,
        "circle-radius": 10,
        "circle-stroke-width": 1,
        "circle-stroke-color": "#fff",
      },
    });

    // labels (short)
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

    // selected highlight layer (initially empty filter)
    map.addLayer({
      id: "selected-point",
      type: "circle",
      source: "unis",
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-color": "#ff6b6b",
        "circle-radius": 14,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#fff",
      },
    });

    // fit bounds if we have features
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

    // single click -> popup
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
          Faculty: ${props.faculty_count ?? 0}<br/>
          <small>Double-click for details</small>
        </div>`;

      popupRef.value = new maplibregl.Popup({
        offset: 14,
        closeButton: true,
        className: "map-popup",
        maxWidth: POPUP_MAX_WIDTH,
      })
        .setLngLat(coords as [number, number])
        .setHTML(html)
        .addTo(map);
    });

    // cluster click -> expand
    map.on("click", "clusters", (e) => {
      const features = map!.queryRenderedFeatures(e.point, {
        layers: ["clusters"],
      });
      if (!features.length) return;
      const clusterId = features[0].properties.cluster_id;
      const source = map!.getSource("unis") as maplibregl.GeoJSONSource;
      source.getClusterExpansionZoom(clusterId, (err, zoom) => {
        if (err) return;
        map!.easeTo({
          center: (features[0].geometry as any).coordinates,
          zoom,
          duration: 500,
        });
      });
    });

    // dblclick -> lazy load details and open side panel
    map.on("dblclick", "points", async (e) => {
      e.originalEvent?.preventDefault();
      const feature = e.features?.[0];
      if (!feature) return;
      const id = (feature.properties as any).id as string;

      // if cached -> show
      if (detailsCache.has(id)) {
        selectedUniversity.value = detailsCache.get(id)!;
        visibleCount.value = FAC_SLAB;
        selectedId.value = id;
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
        updateSelectedFilter(id);
      } catch (err) {
        console.error("Failed to load details for", id, err);
        selectedUniversity.value = null;
      } finally {
        detailLoading.value = false;
      }
    });

    // cursor changes
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

// update the selected-point filter to visually highlight
function updateSelectedFilter(id: string | null) {
  if (!map) return;
  const filter = id ? ["==", ["get", "id"], id] : ["==", ["get", "id"], ""];
  try {
    map.setFilter("selected-point", filter);
  } catch (e) {
    // layer may not be added yet
  }
}

// search handlers
const onSearchInput = debounce(() => {
  // intentionally empty - keep light; use Enter to trigger searchAndFly
}, 300);

function searchAndFly() {
  if (!map) return;
  const q = search.value.trim().toLowerCase();
  if (!q) return;
  for (const [id, u] of universitiesById) {
    if (u.name.toLowerCase().includes(q)) {
      map.easeTo({ center: [u.longitude, u.latitude], zoom: 8, duration: 700 });
      // background prefetch details
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

// side panel helpers
function showMoreFaculty() {
  visibleCount.value += FAC_SLAB;
}
function closePanel() {
  selectedUniversity.value = null;
  selectedId.value = null;
  updateSelectedFilter(null);
}

// watch for selectedId to keep highlight in sync if changed programmatically
watch(selectedId, (id) => updateSelectedFilter(id ?? null));

// cleanup
onBeforeUnmount(() => {
  popupRef.value?.remove();
  map?.remove();
});
</script>

<style scoped>
.app {
  height: 100vh;
  width: 100vw;
  position: relative;
  font-family: Inter, Arial, sans-serif;
}

/* map area leaves space for side panel */
.map-container {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  right: 360px;
}

/* controls */
.controls {
  position: absolute;
  left: 12px;
  top: 12px;
  z-index: 11;
}
.search {
  padding: 8px 10px;
  width: 260px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
}

/* side panel */
.side-panel {
  position: absolute;
  right: 0;
  top: 0;
  width: 360px;
  height: 100%;
  background: #fff;
  border-left: 1px solid #eee;
  padding: 18px;
  overflow: auto;
  z-index: 12;
}
.side-panel .close {
  float: right;
  font-size: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
}
.loading {
  font-style: italic;
  color: #666;
}

/* faculty list */
.faculty-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 55vh;
  overflow: auto;
}
.fac-row {
  padding: 10px 0;
  border-bottom: 1px dashed #eee;
}
.fac-name a {
  color: #1565c0;
  text-decoration: none;
  font-weight: 600;
}
.fac-dept {
  font-size: 12px;
  color: #666;
}
.more-btn {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
}

/* popup styling — make it larger and readable */
.map-popup {
  font-family: Arial, sans-serif;
  min-width: 240px;
  max-width: 520px;
  line-height: 1.2;
}
</style>
