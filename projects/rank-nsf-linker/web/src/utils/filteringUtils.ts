import axios from "axios";
import maplibregl from "maplibre-gl";
import type { Ref } from "vue";

import type { UniSummary } from "@/models/models";
import { errorHandler } from "@/utils/errorHandlingUtils";
import { buildFeatureCollection } from "@/utils/coloringUtils";
import { updatePointsLayer } from "@/utils/coloringUtils";
import { CLUSTER_RADIUS } from "@/config/styleConfig";

export async function fetchAllSummaries(
  onCountryDone: (data: UniSummary[]) => void
) {
  try {
    // Fetch top US universities from new endpoint
    const response = await axios.get<UniSummary[]>(
      "/api/universities/top?limit=100"
    );
    const data = response.data;
    onCountryDone(data);
    return data;
  } catch (err: any) {
    errorHandler(err, "Failed to fetch top universities");
    return [];
  }
}

export async function setupMapWithSummaries(
  pipelineStatusMessage: Ref<string>,
  map: maplibregl.Map
) {
  let summaries: UniSummary[] = [];
  const universitiesById = new Map<string, UniSummary>();
  await fetchAllSummaries((data) => {
    if (!map) return;

    summaries.push(...data);

    const fc = buildFeatureCollection(universitiesById, summaries);

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
    updatePointsLayer(map);

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
      // const id = (feature.properties as any).id as string;
      // await selectUniversity(id);
    });

    ["points", "clusters"].forEach((layer) => {
      map!.on(
        "mouseenter",
        layer,
        () => (map!.getCanvas().style.cursor = "pointer")
      );
      map!.on("mouseleave", layer, () => (map!.getCanvas().style.cursor = ""));
    });
  });

  pipelineStatusMessage.value = "completed";
}
