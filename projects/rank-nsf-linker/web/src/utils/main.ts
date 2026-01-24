import type { Ref } from "vue";
import axios from "axios";
import maplibregl from "maplibre-gl";

import { errorHandler } from "@/utils/errorHandlingUtils";
import { setupMapWithSummaries } from "@/utils/filteringUtils";

// Extract these as separate methods
export async function initializeMap(
  mapContainer: Ref<HTMLDivElement | null>,
  map: Ref<any>
) {
  console.log("🗺️ Initializing map...");

  if (!mapContainer.value) {
    throw new Error("Map container not found");
  }

  map.value = new maplibregl.Map({
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {
        "carto-tiles": {
          type: "raster",
          tiles: [
            "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
            "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors © CARTO",
        },
      },
      layers: [{ id: "carto-tiles", type: "raster", source: "carto-tiles" }],
    },
    center: [-95, 37],
    zoom: 4,
  });

  map.value.doubleClickZoom.disable();
  map.value.addControl(
    new maplibregl.NavigationControl({ showCompass: true }),
    "top-left"
  );
  map.value.addControl(new maplibregl.FullscreenControl(), "top-left");
}

async function checkBackendHealth() {
  try {
    await axios.get("/api/health");
    return { status: "completed", shouldRetry: false };
  } catch (err) {
    return handleHealthCheckError(err);
  }
}

function handleHealthCheckError(err: any) {
  if (!axios.isAxiosError(err) || !err.response) {
    console.error("❗ Unexpected error while checking backend:", err);
    return { status: "unknown", shouldRetry: true, retryAfter: 3 };
  }

  const serverStatus = err.response.headers["server-status"] || "";
  const parts = serverStatus.split("/");
  const currentStatus = parts[1] || serverStatus;
  const retryAfter = parseInt(err.response.headers["Retry-After"], 10) || 3;

  if (currentStatus === "failed") {
    errorHandler(
      new Error("Backend pipeline failed"),
      "Error fetching university summaries"
    );
    return { status: "failed", shouldRetry: false };
  }

  if (currentStatus === "in-progress") {
    return { status: "in-progress", shouldRetry: true, retryAfter };
  }

  console.warn(
    `⚠️ Received unknown backend status: "${currentStatus}". Retrying in ${retryAfter}s.`
  );
  return { status: currentStatus, shouldRetry: true, retryAfter };
}

export async function waitForBackendReady(pipelineStatusMessage: Ref<string>) {
  let attempt = 0;

  while (
    pipelineStatusMessage.value === "in-progress" ||
    !pipelineStatusMessage.value ||
    pipelineStatusMessage.value === ""
  ) {
    attempt++;
    console.log(`🔁 [Attempt ${attempt}] Checking backend health...`);

    const result = await checkBackendHealth();
    pipelineStatusMessage.value = result.status;

    if (!result.shouldRetry) {
      break;
    }

    await new Promise((resolve) => setTimeout(resolve, 60 * 1000));
  }
}

export async function loadMapData(
  pipelineStatusMessage: Ref<string>,
  map: Ref<any>
) {
  console.log("🚀 Starting map data setup...");

  try {
    if (!map.value) {
      throw new Error("Map instance is not initialized");
    }
    await setupMapWithSummaries(pipelineStatusMessage, map.value);
    console.log("🎉 Map data successfully loaded and rendered.");
  } catch (err) {
    handleMapSetupError(pipelineStatusMessage, err);
  }
}

function handleMapSetupError(pipelineStatusMessage: Ref<string>, err: any) {
  if (!axios.isAxiosError(err) || !err.response) {
    console.error("❗ Unexpected error during map setup:", err);
    errorHandler(err, "Error fetching university summaries");
    return;
  }

  const httpStatus = err.response.status;
  console.error(`❌ Axios error during setup: HTTP ${httpStatus}`);

  if (httpStatus === 500) {
    pipelineStatusMessage.value = "failed";
    errorHandler(
      new Error("Backend service is unavailable (500)"),
      "Error fetching university summaries"
    );
  } else if (httpStatus === 503) {
    pipelineStatusMessage.value = "in-progress";
    console.warn("⚠️ Backend still in progress (503).");
  }
}
