// src/config/mapSettings.ts
import { ref, watch } from "vue";

import { getStoredCountry, setStoredCountry } from "@/utils/storageUtils";
import {
  COUNTRIES,
  type BoundedCountry,
  toMapboxBounds,
} from "@/config/countries";
import { logger } from "@/utils/logger";
import { setupMapWithSummaries } from "@/utils/filteringUtils";

// Shared map reference
export const mapInstance = ref<mapboxgl.Map | null>(null);

// Selected country
export const selectedCountry = ref<string>(getStoredCountry());

// Country lock state
export const isCountryLocked = ref(false);

watch(selectedCountry, async (countryCode) => {
  if (!countryCode || !mapInstance.value) return;

  const country = COUNTRIES.find((c: BoundedCountry) => c.code === countryCode);

  if (!country?.bounds) {
    logger.warn("Country not found or missing bounds", { countryCode });
    return;
  }

  const map = mapInstance.value;

  logger.info("Starting country transition", {
    from: map.getCenter(),
    to: country.name,
  });

  // Save preference immediately
  setStoredCountry(countryCode);

  // Remove bounds for smooth animation
  map.setMaxBounds(null as any);

  const currentZoom = map.getZoom();
  const intermediateZoom = Math.min(currentZoom, country.zoom, 2);

  // Phase 1: Zoom out
  await new Promise<void>((resolve) => {
    map.once("zoomend", () => resolve());
    map.easeTo({
      zoom: intermediateZoom,
      duration: 600,
      easing: (t: number) => t * (2 - t),
    });
  });

  // Phase 2: Pan to destination
  await new Promise<void>((resolve) => {
    map.once("moveend", () => resolve());
    map.easeTo({
      center: [country.longitude, country.latitude],
      duration: 1200,
      easing: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
    });
  });

  // Phase 3: Load new data (while zooming in)
  const dataLoadPromise = setupMapWithSummaries(map, countryCode);

  // Phase 4: Zoom in to target (runs in parallel with data load)
  const zoomPromise = new Promise<void>((resolve) => {
    map.once("zoomend", () => resolve());
    map.easeTo({
      zoom: country.zoom,
      duration: 800,
      easing: (t: number) => 1 - Math.pow(1 - t, 3),
    });
  });

  // Wait for both to complete
  await Promise.all([dataLoadPromise, zoomPromise]);

  // Apply bounds after everything is done
  map.setMaxBounds(toMapboxBounds(country.bounds));

  logger.info("Country transition complete", { country: country.name });
});
