// utils/mapInteractions.ts
import mapboxgl from "mapbox-gl";
import type { UniSummary, Faculty } from "@/models/models";
import { logger } from "@/utils/logger";

const interactionLogger = logger.child("MapInteractions");

export function setupMapInteractions(
  map: any,
  universitiesById: Map<string, UniSummary>
) {
  interactionLogger.debug("Setting up map interactions", {
    totalUniversities: universitiesById.size,
  });

  // Tooltip on hover
  const tooltip = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false,
    className: "map-tooltip",
  });

  interactionLogger.debug("Tooltip instance created");

  map.on("mouseenter", "university-points", (e: any) => {
    map.getCanvas().style.cursor = "pointer";

    const feature = e.features[0];
    const uniId = feature.properties.id;

    interactionLogger.debug("Mouse entered point", { uniId });

    const uni = universitiesById.get(uniId);

    if (!uni) {
      interactionLogger.warn("University not found in map", { uniId });
      return;
    }

    const facultyCount = uni.faculty?.length || 0;

    interactionLogger.debug("Showing tooltip", {
      university: uni.institution,
      facultyCount,
    });

    tooltip
      .setLngLat(feature.geometry.coordinates)
      .setHTML(
        `
        <div class="tooltip-content">
          <strong>${uni.institution}</strong>
          <div class="faculty-count">${facultyCount} faculty member${
          facultyCount !== 1 ? "s" : ""
        }</div>
        </div>
      `
      )
      .addTo(map);
  });

  map.on("mouseleave", "university-points", () => {
    interactionLogger.debug("Mouse left point, removing tooltip");
    map.getCanvas().style.cursor = "";
    tooltip.remove();
  });

  // Popup on click
  map.on("click", "university-points", (e: any) => {
    interactionLogger.time("renderPopup");

    const feature = e.features[0];
    const uniId = feature.properties.id;

    interactionLogger.debug("Point clicked", { uniId });

    const uni = universitiesById.get(uniId);

    if (!uni) {
      interactionLogger.error("University not found for popup", uniId);
      return;
    }

    interactionLogger.debug("Building popup for university", {
      institution: uni.institution,
      region: uni.region,
      facultyCount: uni.faculty?.length || 0,
    });

    // Build faculty list HTML
    const facultyHTML =
      uni.faculty
        ?.map((f: Faculty, index: number) => {
          const metrics = [];
          if (f.citations !== undefined)
            metrics.push(`${f.citations} citations`);
          if (f.publications !== undefined)
            metrics.push(`${f.publications} pubs`);
          if (f.hindex !== undefined) metrics.push(`h-index: ${f.hindex}`);

          if (index === 0) {
            interactionLogger.debug("First faculty member", {
              name: f.name,
              homepage: f.homepage,
              metricsCount: metrics.length,
              interestsCount: f.interests?.length || 0,
              areasCount: f.matched_areas?.length || 0,
            });
          }

          return `
        <li class="faculty-item">
          <div class="faculty-name">
            ${
              f.homepage
                ? `<a href="${f.homepage}" target="_blank" rel="noopener">${f.name}</a>`
                : `<span>${f.name}</span>`
            }
          </div>
          
          ${
            metrics.length > 0
              ? `<div class="faculty-metrics">${metrics.join(" • ")}</div>`
              : ""
          }
          
          ${
            f.interests?.length
              ? `<div class="faculty-interests">
                <strong>Interests:</strong> ${f.interests.join(", ")}
               </div>`
              : ""
          }
          
          ${
            f.matched_areas?.length
              ? `<div class="faculty-areas">
                <strong>Areas:</strong> ${f.matched_areas.join(", ")}
               </div>`
              : ""
          }
        </li>
      `;
        })
        .join("") || '<li class="no-data">No faculty data available</li>';

    if (!uni.faculty || uni.faculty.length === 0) {
      interactionLogger.warn("No faculty data available for university", {
        institution: uni.institution,
      });
    }

    const popupHTML = `
      <div class="university-popup">
        <h3>${uni.institution}</h3>
        ${uni.region ? `<div class="uni-location">${uni.region}</div>` : ""}
        <hr>
        <div class="faculty-list">
          <ul>${facultyHTML}</ul>
        </div>
      </div>
    `;

    interactionLogger.debug("Popup HTML generated", {
      htmlLength: popupHTML.length,
      hasFaculty: !!uni.faculty?.length,
    });

    try {
      new mapboxgl.Popup({
        maxWidth: "450px",
        className: "university-detail-popup",
      })
        .setLngLat(feature.geometry.coordinates)
        .setHTML(popupHTML)
        .addTo(map);

      interactionLogger.debug("Popup displayed successfully", {
        institution: uni.institution,
      });

      interactionLogger.timeEnd("renderPopup");
    } catch (error) {
      interactionLogger.error("Failed to display popup", error as Error, {
        institution: uni.institution,
      });
    }
  });

  // Cluster click - zoom in
  map.on("click", "clusters", (e: any) => {
    interactionLogger.debug("Cluster clicked");

    const features = map.queryRenderedFeatures(e.point, {
      layers: ["clusters"],
    });

    if (!features || features.length === 0) {
      interactionLogger.warn("No cluster features found at click point");
      return;
    }

    const clusterId = features[0].properties.cluster_id;
    const pointCount = features[0].properties.point_count;

    interactionLogger.debug("Processing cluster click", {
      clusterId,
      pointCount,
    });

    map
      .getSource("unis")
      .getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
        if (err) {
          interactionLogger.error("Failed to get cluster expansion zoom", err);
          return;
        }

        interactionLogger.debug("Zooming to cluster", {
          clusterId,
          targetZoom: zoom,
          center: features[0].geometry.coordinates,
        });

        map.easeTo({
          center: features[0].geometry.coordinates,
          zoom: zoom,
          duration: 800,
        });

        interactionLogger.debug("Cluster zoom animation started");
      });
  });

  interactionLogger.debug("Map interactions setup complete", {
    listeners: ["mouseenter", "mouseleave", "click:points", "click:clusters"],
  });
}
