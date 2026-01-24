import { ref } from "vue";

export const PIPELINE_STATUS = {
  PENDING: "pending",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  FAILED: "failed",
} as const;

export type PipelineStatusType =
  (typeof PIPELINE_STATUS)[keyof typeof PIPELINE_STATUS];

export const STATUS_CONFIG = {
  [PIPELINE_STATUS.PENDING]: {
    message: "Rendering map...",
    showOverlay: true,
  },
  [PIPELINE_STATUS.IN_PROGRESS]: {
    message: "The server is currently being updated. Please wait...",
    showOverlay: true,
  },
  [PIPELINE_STATUS.FAILED]: {
    message:
      "Server has run into an issue. Please reach out at saifulislam84210@gmail.com",
    showOverlay: true,
  },
  [PIPELINE_STATUS.COMPLETED]: {
    message: "",
    showOverlay: false,
  },
} as const;

export type StatusConfig = typeof STATUS_CONFIG;

export const VIZ_MODES = {
  AREA: "area" as const,
  FUNDING: "funding" as const,
  FACULTY: "faculty" as const,
  NSF: "nsf" as const,
} as const;

export type VizMode = (typeof VIZ_MODES)[keyof typeof VIZ_MODES];
export const vizMode = ref<VizMode>(VIZ_MODES.AREA);
