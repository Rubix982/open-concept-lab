import axios from "axios";
import type { UniSummary } from "@/models/models";
import { errorHandler } from "@/utils/errorHandlingUtils";
import { setupMapInteractions } from "./mapInteractions";
import { logger } from "./logger";

export async function fetchAllSummaries(
  onCountryDone: (data: UniSummary[]) => void,
  country: string
) {
  try {
    // Fetch top US universities from new endpoint
    const response = await axios.get<UniSummary[]>(
      `/api/universities/top?limit=100&country=${country}`
    );
    const data = response.data;
    onCountryDone(data);
    return data;
  } catch (err: any) {
    errorHandler(err, "Failed to fetch top universities");
    return [];
  }
}

export async function setupMapWithSummaries(map: any, countryCode: string) {
  const mapLogger = logger.child("MapSetup");

  mapLogger.info("Setting up map for country", { countryCode });

  removeExistingMapData(map);

  const universitiesById = new Map<string, UniSummary>();

  await fetchAllSummaries((data) => {
    if (!map) {
      mapLogger.error("Map not initialized");
      return;
    }

    mapLogger.debug("Fetched universities", {
      count: data.length,
      countryCode,
    });

    map.addSource("universities", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: data.map((uni) => ({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [uni.longitude, uni.latitude],
          },
          properties: {
            id: uni.institution,
            name: uni.institution,
            funding: uni.funding,
            top_area: uni.top_area ?? "Other",
            label: shortLabel(uni.institution),
            faculty_count: uni.faculty_count ?? 0,
          },
        })),
      },
    });

    data.forEach((uni) => {
      universitiesById.set(uni.institution, uni);
    });
    setupMapInteractions(map, universitiesById);

    map.addLayer({
      id: "university-points",
      type: "circle",
      source: "universities",
      paint: {
        "circle-radius": 8,
        "circle-color": "#3b82f6",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#fff",
      },
    });

    mapLogger.debug("Map setup complete", {
      universities: data.length,
      country: countryCode,
    });
  }, countryCode);
}

function shortLabel(name: string): string {
  if (!name) return "";
  const parts = name.split(/\s+/).slice(0, 3);
  return parts
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 4);
}

// Helper function to remove existing map data
function removeExistingMapData(map: any) {
  const mapLogger = logger.child("MapCleanup");

  // List of layer IDs to remove
  const layersToRemove = [
    "university-points",
    "clusters",
    "cluster-count",
    "point-label",
    "selected-point",
  ];

  // List of source IDs to remove
  const sourcesToRemove = ["universities", "unis"];

  // Remove layers
  layersToRemove.forEach((layerId) => {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
      mapLogger.debug("Removed layer", { layerId });
    }
  });

  // Remove sources
  sourcesToRemove.forEach((sourceId) => {
    if (map.getSource(sourceId)) {
      map.removeSource(sourceId);
      mapLogger.debug("Removed source", { sourceId });
    }
  });

  mapLogger.info("Map cleanup complete");
}
