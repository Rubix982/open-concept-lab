import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

/**
 * A hairline under the navbar that fills as you read. Written to the DOM
 * directly rather than through state, so scrolling never re-renders the post.
 * It is portalled to <body>: an ancestor with a transform (the page's arrival
 * animation) would otherwise become its containing block and drag it down.
 */
export default function ReadingProgress(): ReactNode {
  const bar = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const article = document.querySelector<HTMLElement>(".ocl-article__body");
      if (!article || !bar.current) return;
      const { top, height } = article.getBoundingClientRect();
      const span = height - window.innerHeight;
      const read = span <= 0 ? 1 : Math.min(1, Math.max(0, -top / span));
      bar.current.style.transform = `scaleX(${read})`;
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [mounted]);

  if (!mounted) return null;
  return createPortal(
    <div className="ocl-progress" aria-hidden="true">
      <div className="ocl-progress__bar" ref={bar} />
    </div>,
    document.body,
  );
}
