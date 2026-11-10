import { useSyncExternalStore } from "react";

/**
 * Which view of a paper page is showing — shared by the switch and the rail.
 *
 * The switch and the contents rail sit in different branches of the tree with
 * no common ancestor either of them owns, and the body between them is raw MDX.
 * Lifting the state would mean swizzling the doc layout to wrap markup that
 * neither view controls, so it lives here instead and both subscribe.
 *
 * Two fields rather than one, because the switch and the body answer on
 * different beats: `pending` is what the reader just pressed and the button
 * lights up on it at once, `view` is what is on screen and changes only once
 * the outgoing content has faded. Collapsing them would make the button feel
 * dead for the length of the fade.
 */
export type View = "paper" | "threads";
export type ViewState = { view: View; pending: View };

/** Long enough to read as a fade, short enough not to be a wait. */
export const SWAP_MS = 150;

const INITIAL: ViewState = Object.freeze({ view: "paper", pending: "paper" });

let state: ViewState = INITIAL;
const subscribers = new Set<() => void>();

function commit(next: ViewState): void {
  state = next;
  subscribers.forEach((fn) => fn());
}

function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => {
    subscribers.delete(fn);
  };
}

const reduced = (): boolean =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;

let timer: ReturnType<typeof setTimeout> | undefined;

export function requestView(next: View): void {
  if (next === state.pending) return;
  clearTimeout(timer);
  commit({ view: state.view, pending: next });
  timer = setTimeout(
    () => commit({ view: next, pending: next }),
    reduced() ? 0 : SWAP_MS,
  );
}

/** Back to the paper. Called when the switch unmounts, i.e. on leaving the page. */
export function resetView(): void {
  clearTimeout(timer);
  state = INITIAL;
  subscribers.forEach((fn) => fn());
}

export function usePaperView(): ViewState {
  return useSyncExternalStore(
    subscribe,
    () => state,
    () => INITIAL,
  );
}
