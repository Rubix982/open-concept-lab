import type { UniSummary } from "@/models/models";
import { AREA_COLORS } from "@/config/styleConfig";
import { VIZ_MODES, vizMode } from "@/config/pipelineStatus";

export function shortLabel(name: string): string {
  if (!name) return "";
  const parts = name.split(/\s+/).slice(0, 3);
  return parts
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 4);
}

export function getAreaColor(area?: string): string {
  return AREA_COLORS[area || "Other"] || AREA_COLORS.Other;
}

export function buildFeatureCollection(
  universitiesById: any,
  summaries: UniSummary[]
) {
  const features = summaries.map((u) => {
    universitiesById.set(u.institution, u);
    return {
      type: "Feature" as const,
      properties: {
        name: u.institution,
        top_area: u.top_area ?? "Other",
        label: shortLabel(u.institution),
        faculty_count: u.faculty_count ?? 0,
        funding: u.funding ?? 0,
        // nsf_awards: u.nsf_awards ?? 0,
      },
      geometry: {
        type: "Point" as const,
        coordinates: [u.longitude, u.latitude],
      },
    };
  });
  return { type: "FeatureCollection" as const, features };
}

export function getMarkerColor(props: any, mode: string): string {
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

export function getMarkerSize(props: any, mode: string): number {
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

export function updatePointsLayer(map: any) {
  if (!map || !map.getLayer("points")) return;

  map.removeLayer("points");

  let circleColor: any;
  let circleRadius: any;

  // Use helper functions to build the MapLibre expressions
  switch (vizMode.value) {
    case VIZ_MODES.AREA:
      circleColor = ["match", ["get", "top_area"]];
      Object.entries(AREA_COLORS).forEach(([k, v]) => {
        circleColor.push(k, v);
      });
      circleColor.push(getMarkerColor({ top_area: "Other" }, "area")); // Default
      circleRadius = getMarkerSize({}, "area");
      break;

    case VIZ_MODES.FUNDING:
      circleColor = [
        "step",
        ["get", "funding"],
        getMarkerColor({ funding: 0 }, "funding"), // Default
        10,
        getMarkerColor({ funding: 11 }, "funding"),
        20,
        getMarkerColor({ funding: 21 }, "funding"),
        50,
        getMarkerColor({ funding: 51 }, "funding"),
        100,
        getMarkerColor({ funding: 101 }, "funding"),
      ];
      circleRadius = [
        "interpolate",
        ["linear"],
        ["get", "funding"],
        0,
        getMarkerSize({ funding: 0 }, "funding"),
        200,
        getMarkerSize({ funding: 200 }, "funding"),
      ];
      break;

    case VIZ_MODES.FACULTY:
      circleColor = [
        "step",
        ["get", "faculty_count"],
        getMarkerColor({ faculty_count: 0 }, "faculty"), // Default
        10,
        getMarkerColor({ faculty_count: 11 }, "faculty"),
        25,
        getMarkerColor({ faculty_count: 26 }, "faculty"),
        50,
        getMarkerColor({ faculty_count: 51 }, "faculty"),
        100,
        getMarkerColor({ faculty_count: 101 }, "faculty"),
      ];
      circleRadius = getMarkerSize({}, "faculty"); // Simplified for now
      break;

    case VIZ_MODES.NSF:
      circleColor = ["step", ["get", "nsf_awards"]]; // Simplified for now
      circleRadius = getMarkerSize({}, "nsf"); // Simplified for now
      break;
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
