import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { useLocation } from "@docusaurus/router";
import { usePluginData } from "@docusaurus/useGlobalData";
import DropdownNavbarItem, { type Props as DropdownProps } from "@theme/NavbarItem/DropdownNavbarItem";
import type { LabData } from "@site/plugins/lab-data";
import { SHIPPED } from "@site/src/data/shipped";
import { TabIcon } from "@site/src/components/TabIcons";

/**
 * The navbar's Making menu: the four stages of a thing I make, drawn as one
 * path from an idea to a tool in use. The line between stops firms up as the
 * work does — dotted, dashed, solid. On a phone it is the theme's plain list.
 */

type Stop = { name: string; line: string; tone: number; count: (d: LabData) => [number, string] };

const STOPS: Record<string, Stop> = {
  "/someday": { name: "someday", tone: 4, line: "Things to do, try, learn or make, one day.", count: (d) => [d.someday.length, "idea"] },
  "/unfinished": { name: "unfinished", tone: 3, line: "Started, then stopped partway.", count: (d) => [d.unfinished.length, "project"] },
  "/built": { name: "built", tone: 1, line: "Pages I made to understand something.", count: (d) => [d.built.length, "page"] },
  "/shipped": { name: "shipped", tone: 2, line: "Tools out in the world, in use.", count: () => [SHIPPED.length, "tool"] },
};

type Item = { to: string; label: string };

function StopCard({ item, current, data }: { item: Item; current: boolean; data: LabData }): ReactNode {
  const stop = STOPS[item.to];
  const art = useBaseUrl(`/img/art/tabs/${stop.name}.svg`);
  const [n, noun] = stop.count(data);
  return (
    <li className={`ocl-making__stop ocl-making__stop--${stop.name} ocl-window--tone${stop.tone}${current ? " is-current" : ""}`}>
      <Link to={item.to} className="ocl-making__link" aria-current={current ? "page" : undefined}>
        <span className="ocl-making__dot">
          <svg className="ocl-making__ring" viewBox="0 0 32 32" aria-hidden="true">
            <circle cx="16" cy="16" r="15" />
          </svg>
          <TabIcon name={stop.name} size={15} />
        </span>
        {current ? <span className="ocl-making__here">you are here</span> : null}
        <span className="ocl-making__art">
          <img src={art} alt="" loading="lazy" decoding="async" />
        </span>
        <span className="ocl-making__name">{item.label}</span>
        <span className="ocl-making__line">{stop.line}</span>
        <span className="ocl-making__count">
          {n} {noun}
          {n === 1 ? "" : "s"}
        </span>
      </Link>
    </li>
  );
}

function MakingDesktop({ label, items }: { label: string; items: Item[] }): ReactNode {
  const data = usePluginData("ocl-lab-data") as LabData;
  const { pathname } = useLocation();
  const base = useBaseUrl("/");
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const closing = useRef<number | undefined>(undefined);
  const hoveredAt = useRef(0);
  const id = useId();

  const isCurrent = (to: string) => {
    const root = base + to.replace(/^\//, "");
    return pathname === root || pathname.startsWith(root + "/");
  };
  const active = items.some((item) => isCurrent(item.to));

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return undefined;
    const away = (e: MouseEvent) => {
      if (!wrap.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", away);
    return () => document.removeEventListener("mousedown", away);
  }, [open]);
  useEffect(() => () => window.clearTimeout(closing.current), []);

  const show = () => {
    window.clearTimeout(closing.current);
    if (!open) hoveredAt.current = Date.now();
    setOpen(true);
  };
  const hide = () => {
    window.clearTimeout(closing.current);
    closing.current = window.setTimeout(() => setOpen(false), 160);
  };

  return (
    <div
      ref={wrap}
      className={`navbar__item ocl-making${open ? " is-open" : ""}`}
      onMouseEnter={show}
      onMouseLeave={hide}
      onBlur={(e) => {
        if (!wrap.current?.contains(e.relatedTarget as Node)) setOpen(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          setOpen(false);
          trigger.current?.focus();
        }
      }}
    >
      <button
        ref={trigger}
        type="button"
        className={`navbar__link ocl-making__trigger${active ? " navbar__link--active" : ""}`}
        aria-expanded={open}
        aria-controls={id}
        // a hover has usually opened it already; the click that follows should not shut it
        onClick={() => setOpen((o) => (o && Date.now() - hoveredAt.current > 400 ? false : true))}
      >
        {label}
        <svg className="ocl-making__caret" viewBox="0 0 10 6" width="10" height="6" aria-hidden="true">
          <path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <div className="ocl-making__panel" id={id} data-open={open}>
        <ol className="ocl-making__path">
          {items.map((item) => (
            <StopCard key={item.to} item={item} current={isCurrent(item.to)} data={data} />
          ))}
        </ol>
      </div>
    </div>
  );
}

export default function MakingMenu(props: DropdownProps): ReactNode {
  if (props.mobile) return <DropdownNavbarItem {...props} />;
  const items = (props.items as Item[]).filter((item) => STOPS[item.to]);
  return <MakingDesktop label={String(props.label ?? "Making")} items={items} />;
}
