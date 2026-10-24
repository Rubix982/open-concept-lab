import { useEffect, useRef, type ReactNode } from "react";

/**
 * A hairline under the navbar that fills as you read. Written to the DOM
 * directly rather than through state, so scrolling never re-renders the post.
 */
export default function ReadingProgress(): ReactNode {
  const bar = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
  }, []);

  return (
    <div className="ocl-progress" aria-hidden="true">
      <div className="ocl-progress__bar" ref={bar} />
    </div>
  );
}
