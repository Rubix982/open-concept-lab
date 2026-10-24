import type { ReactNode } from "react";

/**
 * A piece's status drawn as a stage of growth, after the digital-garden habit
 * of marking how finished a note is. The site's own words stay — draft,
 * provisional, standing, superseded — and the drawing makes them legible at a
 * glance: a seedling, a plant in bud, an evergreen, a stem that has wilted.
 */
const PATHS: Record<string, ReactNode> = {
  draft: (
    <>
      <path d="M8 14V8" />
      <path d="M8 9.5C8 7 6.2 5.6 4 5.6c0 2.4 1.8 3.9 4 3.9Z" />
      <path d="M8 8.5c0-2.3 1.6-3.6 3.6-3.6 0 2.2-1.6 3.6-3.6 3.6Z" />
    </>
  ),
  provisional: (
    <>
      <path d="M8 14V6" />
      <path d="M8 11c0-2-1.6-3.2-3.6-3.2 0 2 1.6 3.2 3.6 3.2Z" />
      <path d="M8 10c0-1.9 1.5-3 3.4-3 0 1.9-1.5 3-3.4 3Z" />
      <path d="M8 6.2c-1.1 0-1.8-.9-1.8-2S8 2 8 2s1.8 1.1 1.8 2.2-.7 2-1.8 2Z" />
    </>
  ),
  standing: (
    <>
      <path d="M8 2 4.6 7h2L3.8 11h8.4L9.4 7h2L8 2Z" />
      <path d="M8 11v3" />
    </>
  ),
  superseded: (
    <>
      <path d="M8 14V9c0-2.6 1.6-4.5 4-4.5" />
      <path d="M12 4.5c.4 1.6-.3 3-1.7 3.4-.3-1.5.4-2.9 1.7-3.4Z" />
    </>
  ),
};

export default function Stage({
  status,
  label = true,
}: {
  status?: string;
  /** Show the status word beside the drawing. */
  label?: boolean;
}): ReactNode {
  if (!status || !PATHS[status]) {
    return null;
  }
  return (
    <span className={`ocl-stage ocl-stage--${status}`}>
      <svg
        className="ocl-stage__icon"
        viewBox="0 0 16 16"
        width="16"
        height="16"
        aria-hidden="true"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {PATHS[status]}
      </svg>
      {label ? <span className="ocl-stage__label">{status}</span> : null}
    </span>
  );
}
