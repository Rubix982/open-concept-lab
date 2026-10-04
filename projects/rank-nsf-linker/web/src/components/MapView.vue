<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import type { UniversitySummary } from "@/api";

const props = defineProps<{
  universities: UniversitySummary[];
  color: string; // the selected line's colour, or ink when areas span lines
  useGoal: boolean; // size by goal matches instead of faculty count
  selectedId: string | null;
}>();
const emit = defineEmits<{ select: [id: string] }>();

const container = ref<HTMLDivElement | null>(null);
let map: mapboxgl.Map | null = null;
let hover: mapboxgl.Popup | null = null;
const ready = ref(false);

function features(): GeoJSON.FeatureCollection {
  const weightOf = (u: UniversitySummary) => (props.useGoal ? u.goal_matches : u.faculty);
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
          geometry: { type: "Point" as const, coordinates: [u.longitude!, u.latitude!] },
          properties: {
            id: u.id,
            name: u.name,
            weight,
            // Dot area is proportional to the weight, relative to the largest in view.
            size: Math.sqrt(weight / max),
            faculty: u.faculty,
            funded: u.funded,
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
  if (!map || !ready.value) return;
  (map.getSource("unis") as mapboxgl.GeoJSONSource).setData(features());
  map.setPaintProperty("unis", "circle-color", props.color);
}

onMounted(() => {
  mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
  map = new mapboxgl.Map({
    container: container.value!,
    style: "mapbox://styles/mapbox/light-v11",
    bounds: [[-125, 24.5], [-66.5, 49.5]], // contiguous US, where NSF and IPEDS data apply
    fitBoundsOptions: { padding: 24 },
    minZoom: 1.5,
    attributionControl: false,
    projection: "mercator",
  });
  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "bottom-right");
  map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-left");

  map.on("load", () => {
    map!.addSource("unis", { type: "geojson", data: features() });
    map!.addLayer({
      id: "unis",
      type: "circle",
      source: "unis",
      paint: {
        "circle-radius": ["case", [">", ["get", "weight"], 0], ["+", 3.5, ["*", 13, ["get", "size"]]], 2.5],
        "circle-color": props.color,
        "circle-opacity": ["case", [">", ["get", "weight"], 0], 0.82, 0.18],
        // R1 universities carry a heavy ink ring.
        "circle-stroke-color": ["case", ["get", "selected"], "#ffffff", ["get", "r1"], "#1D2A3A", "#ffffff"],
        "circle-stroke-width": ["case", ["get", "selected"], 4, ["get", "r1"], 2.2, 1],
      },
    });
    ready.value = true;
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
      ? `${p.goal} faculty with work matching your goal`
      : `${p.faculty} faculty in your areas, ${p.funded} with an active NSF grant`;
    el.append(name, line);
    hover?.remove();
    hover = new mapboxgl.Popup({ closeButton: false, offset: 12, className: "uni-tip" })
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

watch(() => [props.universities, props.color, props.useGoal, props.selectedId], paint);

// Fly to a university chosen from a list.
watch(
  () => props.selectedId,
  (id) => {
    const u = props.universities.find((x) => x.id === id);
    if (map && u?.latitude != null && u.longitude != null) {
      map.easeTo({ center: [u.longitude, u.latitude], zoom: Math.max(map.getZoom(), 5), duration: 600 });
    }
  },
);

onBeforeUnmount(() => map?.remove());
</script>

<template>
  <div ref="container" class="map" role="region" aria-label="Map of universities"></div>
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
