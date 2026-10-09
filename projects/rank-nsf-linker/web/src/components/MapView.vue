<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import mapboxgl from "mapbox-gl";
import { funders, fundersFor } from "@/store";
import "mapbox-gl/dist/mapbox-gl.css";
import type { UniversitySummary } from "@/api";

const props = defineProps<{
  universities: UniversitySummary[];
  color: string; // the selected line's colour, or ink when areas span lines
  useGoal: boolean; // size by goal matches instead of faculty count
  goalLabel?: string; // what goal_matches counts, for the tooltip (default: matching faculty)
  selectedId: string | null;
  focus?: { key: string; ids: string[] }; // fit the map to these universities when key changes
  countries?: string[]; // every country with universities listed (shading ignores the filters)
}>();
const emit = defineEmits<{ select: [id: string] }>();

const container = ref<HTMLDivElement | null>(null);
let map: mapboxgl.Map | null = null;
let hover: mapboxgl.Popup | null = null;
const ready = ref(false);

function features(): GeoJSON.FeatureCollection {
  const weightOf = (u: UniversitySummary) =>
    props.useGoal ? u.goal_matches : u.faculty;
  const max = Math.max(1, ...props.universities.map(weightOf));
  return {
    type: "FeatureCollection",
    features: props.universities
      .filter((u) => u.latitude !== null && u.longitude !== null)
      .map((u) => {
        const weight = weightOf(u);
        return {
          type: "Feature" as const,
          id: u.id,
          geometry: {
            type: "Point" as const,
            coordinates: [u.longitude!, u.latitude!],
          },
          properties: {
            id: u.id,
            name: u.name,
            weight,
            // Dot area is proportional to the weight, relative to the largest in view.
            size: Math.sqrt(weight / max),
            faculty: u.faculty,
            funded: u.funded,
            // no grant data loaded for this country: say so rather than "0 with a grant"
            covered: fundersFor(u.country).length > 0,
            goal: u.goal_matches,
            r1: u.carnegie === "R1",
            selected: u.id === props.selectedId,
          },
        };
      })
      // Draw big dots first so small ones stay clickable on top.
      .sort((a, b) => b.properties.weight - a.properties.weight),
  };
}

function paint() {
  if (!map?.getSource("unis")) return;
  (map.getSource("unis") as mapboxgl.GeoJSONSource).setData(features());
  map.setPaintProperty("unis", "circle-color", props.color);
  shadeCountries();
}

// ---- base map: Mapbox "light", recoloured so water, land and borders read at a glance ----
const WATER = "#a9cbe3";
const LAND = "#f2f2ec";
const LISTED = "#dde8d2"; // a country with universities in Advisor Atlas
const FUNDED = "#bcd6b0"; // ... and grant data loaded for it
const BORDER = "#5d6876";

function restyleBase() {
  if (!map) return;
  const set = (layer: string, prop: string, value: unknown) => {
    if (map!.getLayer(layer))
      map!.setPaintProperty(layer, prop as never, value as never);
  };
  set("land", "background-color", LAND);
  set("water", "fill-color", WATER);
  set("waterway", "line-color", WATER);
  set("admin-0-boundary", "line-color", BORDER);
  set("admin-0-boundary", "line-width", [
    "interpolate",
    ["linear"],
    ["zoom"],
    1,
    0.8,
    5,
    1.6,
    8,
    2.2,
  ]);
  set("admin-0-boundary-disputed", "line-color", BORDER);
  set("admin-1-boundary", "line-color", "#a7b0ba");
  set("country-label", "text-color", "#3b4654");
  // Countries shaded by what Advisor Atlas holds for them.
  map.addSource("countries", {
    type: "vector",
    url: "mapbox://mapbox.country-boundaries-v1",
  });
  // under water, so lakes stay blue, and under borders and labels
  const below = map.getLayer("water") ? "water" : undefined;
  map.addLayer(
    {
      id: "country-shade",
      type: "fill",
      source: "countries",
      "source-layer": "country_boundaries",
      // one worldview, so disputed areas aren't drawn twice
      filter: [
        "any",
        ["==", ["get", "worldview"], "all"],
        ["in", "US", ["get", "worldview"]],
      ],
      paint: { "fill-color": LAND, "fill-opacity": 1 },
    },
    below,
  );
}

function shadeCountries() {
  if (!map?.getLayer("country-shade")) return;
  // every country listed, not only the filtered ones
  const listed = new Set(
    (props.countries ?? props.universities.map((u) => u.country ?? ""))
      .filter(Boolean)
      .map((c) => c.toUpperCase()),
  );
  const funded = [...listed].filter((c) => fundersFor(c).length);
  const plain = [...listed].filter((c) => !fundersFor(c).length);
  const expr: unknown[] = ["match", ["get", "iso_3166_1"]];
  if (funded.length) expr.push(funded, FUNDED);
  if (plain.length) expr.push(plain, LISTED);
  expr.push(LAND);
  map.setPaintProperty(
    "country-shade",
    "fill-color",
    (expr.length > 3 ? expr : LAND) as never,
  );
}
// Which countries have grant data arrives with /explorer/funders, possibly after the first paint.
watch(funders, shadeCountries);
watch(() => props.countries, shadeCountries);

onMounted(() => {
  mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
  map = new mapboxgl.Map({
    container: container.value!,
    style: "mapbox://styles/mapbox/light-v11",
    bounds: [
      [-125, 24.5],
      [-66.5, 49.5],
    ], // contiguous US, where NSF and IPEDS data apply
    fitBoundsOptions: { padding: 24 },
    minZoom: 1.5,
    attributionControl: false,
    projection: "mercator",
    // Keep tiles already seen (this region, the world view below) instead of the default few
    // screens' worth, so zooming back out or returning to a region doesn't wait on the network.
    minTileCacheSize: 800,
  });
  // A shared link (?u=...) opens with a university selected: start the map there, not on the US.
  const start = props.universities.find((x) => x.id === props.selectedId);
  if (start?.latitude != null && start.longitude != null) {
    map.jumpTo({ center: [start.longitude, start.latitude], zoom: 5 });
  }
  map.addControl(
    new mapboxgl.NavigationControl({ showCompass: false }),
    "bottom-right",
  );
  map.addControl(
    new mapboxgl.AttributionControl({ compact: true }),
    "bottom-left",
  );

  // Opening flight: the map starts on the whole world and flies in to the start view. On the way it
  // loads the tiles of every zoom level in between, which stay cached (minTileCacheSize), so a later
  // zoom-out has a coarser tile to show at once instead of blank land while sharper ones load.
  // Same map and session: no extra map load on the Mapbox bill.
  const startView = { center: map.getCenter(), zoom: map.getZoom() };
  map.jumpTo({ center: [20, 25], zoom: map.getMinZoom() });
  const land = () => (ready.value = true); // focus waits: a fitBounds mid-flight would be cut off
  map.once("load", () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      map!.jumpTo(startView);
      land();
      return;
    }
    let flown = false;
    const fly = () => {
      if (flown || !map) return;
      flown = true;
      map.once("moveend", land); // also when the student grabs the map mid-flight
      map.flyTo({ ...startView, duration: 1800, essential: false });
    };
    map!.once("idle", fly); // the world's tiles first, so the flight starts on a drawn map
    setTimeout(fly, 1200);
  });

  map.on("load", () => {
    restyleBase();
    map!.addSource("unis", { type: "geojson", data: features() });
    map!.addLayer({
      id: "unis",
      type: "circle",
      source: "unis",
      paint: {
        "circle-radius": [
          "case",
          [">", ["get", "weight"], 0],
          ["+", 3.5, ["*", 13, ["get", "size"]]],
          2.5,
        ],
        "circle-color": props.color,
        "circle-opacity": ["case", [">", ["get", "weight"], 0], 0.82, 0.07],
        "circle-stroke-opacity": ["case", [">", ["get", "weight"], 0], 1, 0.15],
        // R1 universities carry a heavy ink ring.
        "circle-stroke-color": [
          "case",
          ["get", "selected"],
          "#ffffff",
          ["get", "r1"],
          "#1D2A3A",
          "#ffffff",
        ],
        "circle-stroke-width": [
          "case",
          ["get", "selected"],
          4,
          ["get", "r1"],
          2.2,
          1,
        ],
      },
    });
    paint();
  });

  map.on("mouseenter", "unis", (e) => {
    map!.getCanvas().style.cursor = "pointer";
    const f = e.features?.[0];
    if (!f) return;
    const p = f.properties as Record<string, any>;
    const el = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = p.name;
    const line = document.createElement("div");
    line.textContent = props.useGoal
      ? `${p.goal} ${props.goalLabel ?? "faculty with work matching your goal"}`
      : p.covered
        ? `${p.faculty} faculty in your areas, ${p.funded} with an active research grant`
        : `${p.faculty} faculty in your areas; no grant data for this country yet`;
    el.append(name, line);
    hover?.remove();
    hover = new mapboxgl.Popup({
      closeButton: false,
      offset: 12,
      className: "uni-tip",
    })
      .setLngLat((f.geometry as GeoJSON.Point).coordinates as [number, number])
      .setDOMContent(el)
      .addTo(map!);
  });
  map.on("mouseleave", "unis", () => {
    map!.getCanvas().style.cursor = "";
    hover?.remove();
  });
  map.on("click", "unis", (e) => {
    const id = e.features?.[0]?.properties?.id;
    if (id) emit("select", id);
  });
});

watch(
  () => [props.universities, props.color, props.useGoal, props.selectedId],
  paint,
);

// A new search: fit the map to the universities with matches.
let lastFocus = "";
// Also called once the map has loaded: a shared link (?q=… or ?country=…) sets the focus before that.
function applyFocus() {
  const f = props.focus;
  if (
    !map ||
    !ready.value ||
    !f ||
    !f.key ||
    !f.ids.length ||
    f.key === lastFocus
  )
    return;
  lastFocus = f.key;
  const pts = props.universities.filter(
    (u) => f.ids.includes(u.id) && u.latitude != null && u.longitude != null,
  );
  if (!pts.length) return;
  const b = new mapboxgl.LngLatBounds();
  pts.forEach((u) => b.extend([u.longitude!, u.latitude!]));
  map.fitBounds(b, { padding: 60, maxZoom: 7, duration: 700 });
}
watch(() => props.focus, applyFocus, { deep: true });
watch(ready, applyFocus);

// Fly to a university chosen from a list, or asked for by name (a profile's university).
function flyToUniversity(id: string | null) {
  const u = props.universities.find((x) => x.id === id);
  if (map && u?.latitude != null && u.longitude != null) {
    map.easeTo({
      center: [u.longitude, u.latitude],
      zoom: Math.max(map.getZoom(), 5),
      duration: 600,
    });
  }
}
watch(() => props.selectedId, flyToUniversity);
defineExpose({ flyToUniversity });

onBeforeUnmount(() => map?.remove());
</script>

<template>
  <div
    ref="container"
    class="map"
    role="region"
    aria-label="Map of universities"
  ></div>
</template>

<style scoped>
.map {
  width: 100%;
  height: 100%;
}
</style>

<style>
.uni-tip .mapboxgl-popup-content {
  font-family: var(--font);
  font-size: var(--t-xs);
  color: var(--ink);
  padding: 8px 11px 7px;
  border-radius: var(--radius-box);
  box-shadow: 0 2px 10px rgba(29, 42, 58, 0.18);
  max-width: 260px;
}
.uni-tip strong {
  display: block;
  font-size: var(--t-sm);
  font-weight: 800;
  margin-bottom: 2px;
}
</style>
