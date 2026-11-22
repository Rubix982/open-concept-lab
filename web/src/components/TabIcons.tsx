import type { ReactNode } from "react";

/** Tiny line icons for the tabs: one stroke each, drawn at 16px. */
export const TAB_ICONS: Record<string, ReactNode> = {
  writing: <path d="M3 13 6 7l5-4 2 2-4 5-6 3Z M3 13l3.6-3.6" />,
  notebook: <path d="M2.5 3.5Q5 3 8 4v9q-3-1-5.5-.5Z M8 4q3-1 5.5-.5v9Q11 12 8 13" />,
  labs: <path d="M6 2h4M6.8 2v4L3 13h10L9.2 6V2M5 10h6" />,
  reading: <path d="M3 3h7l3 3v7H3Z M5.5 7h5M5.5 9.5h4" />,
  agentic: <path d="M8 2.5a5.5 5.5 0 0 1 5.5 5.5M8 13.5A5.5 5.5 0 0 1 2.5 8M12 6l1.5 2 1.5-2M4 10 2.5 8 1 10" />,
  graphics: <path d="M2.5 13 8 3l5.5 10Z M5.25 8h5.5M5.25 8 8 13l2.75-5" />,
  shipped: <path d="M2 6l6-3 6 3-6 3Z M2 6v5l6 3 6-3V6M8 9v5" />,
  built: <path d="M2.5 13h11M3.5 13V9h3v4M6.5 13V5h3v8M9.5 13V7h3v6" />,
  about: <path d="M8 7.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM3 14c.5-3 2.4-4.5 5-4.5s4.5 1.5 5 4.5" />,
  // three quarters of a ring, the last quarter dotted: started, not closed
  unfinished: (
    <>
      <path d="M8 2.5A5.5 5.5 0 1 1 2.5 8" />
      <path d="M2.5 8A5.5 5.5 0 0 1 8 2.5" strokeDasharray="0.1 2.4" />
    </>
  ),
  someday: <path d="M6 13h4M6.5 11h3M8 2.5a4 4 0 0 0-2.4 7.2c.5.4.9 1 .9 1.3h3c0-.3.4-.9.9-1.3A4 4 0 0 0 8 2.5Z" />,
};

export function TabIcon({ name, size = 16 }: { name: string; size?: number }): ReactNode {
  return (
    <svg
      viewBox="0 0 16 16"
      width={size}
      height={size}
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {TAB_ICONS[name]}
    </svg>
  );
}
