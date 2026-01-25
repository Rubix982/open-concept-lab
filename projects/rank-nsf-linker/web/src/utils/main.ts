import type { Ref } from "vue";
import axios from "axios";
import mapboxgl from "mapbox-gl";

import { errorHandler } from "@/utils/errorHandlingUtils";
import { setupMapWithSummaries } from "@/utils/filteringUtils";
import { PIPELINE_STATUS } from "@/config/pipelineStatus";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

/*
# UI/UX improvements - enumerated

## Visual Polish
1. Loading skeleton instead of blank screen
2. Smooth fade-in transitions when map loads
3. Progress bar during backend initialization
4. Animated university markers on first render
5. Hover state on all interactive elements
6. Drop shadows for depth perception
7. Gradient backgrounds instead of flat colors
8. Rounded corners on all UI elements
9. Icon pack for better visual hierarchy (Lucide/Heroicons)
10. Custom cursor on interactive elements

## Map Interactions
11. Click university → fly to location smoothly
12. Double-click → zoom to university cluster
13. Scroll-based zoom with momentum
14. Drag to pan with inertia
15. Pinch-to-zoom on mobile
16. Keyboard shortcuts (arrow keys to pan, +/- to zoom)
17. Right-click context menu
18. Click outside popup to close
19. Escape key closes popup/modals
20. Auto-center map on selected university

## Information Display
21. Tooltip on marker hover (quick preview)
22. Rich popup with university details
23. Sidebar panel with full university info
24. Comparison view (select 2-3 universities)
25. Mini-map in corner for orientation
26. Search bar with autocomplete
27. Filter panel (by state, funding range, faculty count)
28. Sort options (by funding, faculty, NSF awards)
29. Breadcrumb navigation
30. Stats summary card (total universities, avg funding, etc.)

## Data Visualization
31. Color-coded markers by funding tier
32. Size-scaled markers by faculty count
33. Heatmap mode toggle
34. Cluster view when zoomed out
35. Connection lines between collaborating universities
36. Animated data transitions when switching modes
37. Legend explaining color/size meanings
38. Mini charts in popup (funding trend, faculty growth)
39. Comparison chart overlay
40. Geographic distribution histogram

## Performance & Feedback
41. Loading indicators for each async operation
42. Error messages with retry button
43. Success toast notifications
44. Skeleton loaders for data fetching
45. Debounced search input
46. Lazy load university details
47. Cache frequently accessed data
48. Optimistic UI updates
49. Network status indicator
50. "Back to top" button when scrolled

## Navigation & Controls
51. Zoom controls (+ / - buttons)
52. Reset view button
53. Fullscreen toggle
54. Share current view (copy URL with coordinates)
55. Export map as image
56. Print-friendly view
57. Bookmark favorite universities
58. Recent searches/views
59. Navigation history (back/forward)
60. Minimap for overview

## Personalization
61. Save filter preferences
62. Custom color themes
63. Dark mode toggle
64. Font size adjustment
65. Layout density options (compact/comfortable)
66. Save favorite universities
67. Custom map base layer selection
68. Hide/show UI elements
69. Dashboard widget arrangement
70. Export preferences

## Data Discovery
71. "Explore" mode with guided tour
72. Random university button
73. Nearby universities feature
74. Similar universities suggestion
75. Trending/popular universities
76. Recently added universities
77. Categories/tags filter
78. Advanced search (Boolean operators)
79. Saved searches
80. Quick filters (Top 10, Highest funded, etc.)

## Collaboration Features
81. Generate report from selection
82. Email university list
83. Collaborative annotations
84. Comments on universities
85. Flag incorrect data

## Error Handling
86. Graceful degradation when offline
87. Retry failed requests automatically
88. Clear error messages
89. Fallback UI when data unavailable
90. Network error recovery
91. Timeout handling with user feedback
92. Partial data display
93. "Something went wrong" page
94. Report bug button
95. Contact support link

## Onboarding
96. First-time user tutorial
97. Feature highlights on first visit
98. Interactive walkthrough
99. Tooltips for new features
100. "What's new" modal
101. Help icon with documentation
102. Video tutorial link
103. Keyboard shortcuts guide
104. FAQ section
105. Contextual help

## Performance Indicators
106. Load time display (debug mode)
107. FPS counter (debug mode)
108. Memory usage indicator
109. Active filters count badge
110. Results count display
111. Data freshness indicator
112. API response time
113. Cache hit/miss stats
114. Network request count
115. Render time profiler
*/
export async function initializeMap(
  mapContainer: Ref<HTMLDivElement | null>,
  map: Ref<any>
) {
  console.log("🗺️ Initializing map...");

  if (!mapContainer.value) {
    throw new Error("Map container not found");
  }

  // Check if container is visible
  const { offsetWidth, offsetHeight } = mapContainer.value;
  if (offsetWidth === 0 || offsetHeight === 0) {
    throw new Error("Map container has no dimensions - is it hidden?");
  }

  mapboxgl.accessToken = MAPBOX_TOKEN;
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: `mapbox://styles/mapbox/light-v11`,
    center: [-96, 39],
    zoom: 4,
    fadeDuration: 300,
  });

  console.log(
    `✅ Map instance created. Container size: ${offsetWidth} x ${offsetHeight}.`
  );

  map.value.on("load", () => {
    console.log("✅ Map loaded and rendered");
  });

  map.value.on("error", (e: any) => {
    console.error("❌ Map error:", e.error);
  });

  return new Promise((resolve) => {
    map.value.on("load", () => {
      map.value.doubleClickZoom.disable();
      map.value.addControl(new mapboxgl.FullscreenControl(), "top-left");
      map.value.addControl(
        new mapboxgl.NavigationControl({ showCompass: true }),
        "top-left"
      );
      console.log(`✅ Controls added`);
      resolve(map.value);
    });
  });
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
  console.log(
    `⏳ Waiting for backend to be ready. Pipeline Status ${pipelineStatusMessage.value}`
  );

  while (
    pipelineStatusMessage.value === PIPELINE_STATUS.IN_PROGRESS ||
    pipelineStatusMessage.value === PIPELINE_STATUS.PENDING
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
