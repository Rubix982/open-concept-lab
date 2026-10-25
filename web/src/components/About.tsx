import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";

type Contact = { href: string; icon: string; fill?: boolean; label: string; value: string; note: string; tone: number };

type Room = { to: string; art: string; title: string; text: string; tone: number };

// The words are the ones /about has always used for each tab; only the cards are new.
const ROOMS: Room[] = [
  { to: "/writing", art: "steps/lab-retro", title: "Writing", tone: 4,
    text: "Dated pieces. A note, an argument, a session where something turned out to be wrong. The date is part of what they mean." },
  { to: "/notebook", art: "tabs/notebook", title: "Notebook", tone: 1,
    text: "Living pages, one per project, revised in place so a reader always sees current state." },
  { to: "/labs", art: "tabs/labs", title: "Labs", tone: 2,
    text: "Deployment and security learned one small broken system at a time, as a checklist I tick off." },
  { to: "/reading", art: "tabs/reading", title: "Reading", tone: 6,
    text: "The papers my work rests on, marked by whether I have checked each citation against the paper itself." },
  { to: "/agentic", art: "tabs/agentic", title: "Agentic", tone: 5,
    text: "Tools that keep research moving when nobody is watching, and the boundary they are built around." },
  { to: "/shipped", art: "tabs/shipped", title: "Shipped", tone: 2,
    text: "Tools that are deployed and in use, each with a page of its own." },
  { to: "/built", art: "tabs/built", title: "Built", tone: 3,
    text: "Interactive pages I made to understand something." },
  { to: "/someday", art: "tabs/someday", title: "Someday", tone: 4,
    text: "Things I want to do, try, learn or make, written down so my head can stop holding them. Not plans; lines I no longer have to remember." },
];

function RoomCard({ room }: { room: Room }): ReactNode {
  const src = useBaseUrl(`/img/art/${room.art}.svg`);
  return (
    <Link to={room.to} className={`ocl-room ocl-window--tone${room.tone}`}>
      <span className="ocl-room__art">
        <img src={src} alt="" loading="lazy" decoding="async" />
      </span>
      <span className="ocl-room__title">{room.title} <span aria-hidden="true">→</span></span>
      <span className="ocl-room__text">{room.text}</span>
    </Link>
  );
}

/** What this site is: one card per tab, each with its drawing. */
export function AboutRooms(): ReactNode {
  return (
    <div className="ocl-rooms">
      {ROOMS.map((room) => (
        <RoomCard key={room.to} room={room} />
      ))}
    </div>
  );
}

const QUESTIONS = [
  { q: "Is it true regardless of what I hoped?", tone: "gold" },
  { q: "Does it take prior work one verifiable step further?", tone: "lilac" },
  { q: "Would it still matter to the field if my own vision vanished tomorrow?", tone: "sage" },
];

/** The three questions, as three notes pinned up side by side. */
export function AboutQuestions(): ReactNode {
  return (
    <ol className="ocl-notes ocl-questions">
      {QUESTIONS.map(({ q, tone }, i) => (
        <li key={q} className={`ocl-note ocl-note--${tone}`}>
          <span className="ocl-note__tape" aria-hidden="true" />
          <span className="ocl-note__label">Question {i + 1}</span>
          <span className="ocl-note__text">{q}</span>
        </li>
      ))}
    </ol>
  );
}

const ELSEWHERE: Contact[] = [
  { href: "https://github.com/Rubix982", icon: "M8 1.8a6.2 6.2 0 0 0-2 12.1c.3 0 .4-.1.4-.3v-1.1c-1.7.4-2.1-.8-2.1-.8-.3-.7-.7-.9-.7-.9-.6-.4 0-.4 0-.4.6 0 1 .6 1 .6.5.9 1.4.7 1.8.5 0-.4.2-.7.4-.8-1.4-.2-2.8-.7-2.8-3 0-.7.2-1.2.6-1.6 0-.2-.3-.8.1-1.7 0 0 .5-.2 1.7.6a6 6 0 0 1 3.1 0c1.2-.8 1.7-.6 1.7-.6.3.9.1 1.5.1 1.7.4.4.6 1 .6 1.6 0 2.3-1.4 2.8-2.8 3 .2.2.4.6.4 1.1v1.7c0 .2.1.4.4.3A6.2 6.2 0 0 0 8 1.8Z",
    fill: true, label: "GitHub", value: "github.com/Rubix982", note: "Code for the projects written about here", tone: 1 },
  { href: "https://www.linkedin.com/in/suislam", icon: "M3 6h2.2v7H3Zm1.1-3.4a1.3 1.3 0 1 1 0 2.6 1.3 1.3 0 0 1 0-2.6ZM6.6 6h2.1v1c.3-.6 1-1.2 2.2-1.2 2.3 0 2.7 1.5 2.7 3.5V13h-2.2V9.7c0-.8 0-1.8-1.1-1.8s-1.3.9-1.3 1.8V13H6.6Z",
    fill: true, label: "LinkedIn", value: "linkedin.com/in/suislam", note: "Work history and the formal version", tone: 6 },
  { href: "https://github.com/Rubix982/dotclaude/blob/main/CLAUDE.md", icon: "M5 4 1.5 8 5 12 M11 4l3.5 4L11 12 M9.5 2.5l-3 11",
    label: "dotclaude", value: "Rubix982/dotclaude", note: "The instructions my AI agents work under", tone: 5 },
  { href: "mailto:saifulislam84210@gmail.com", icon: "M2 4h12v8H2Z M2 4.5l6 4.5 6-4.5",
    label: "Email", value: "saifulislam84210@gmail.com", note: "The fastest route, corrections included", tone: 4 },
];

/** Where else to find me, as three cards with their own little icon. */
export function AboutElsewhere(): ReactNode {
  return (
    <div className="ocl-elsewhere">
      {ELSEWHERE.map((e) => (
        <a
          key={e.label}
          href={e.href}
          className={`ocl-elsewhere__card ocl-window--tone${e.tone}`}
          {...(e.href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
        >
          <span className="ocl-elsewhere__icon" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="20" height="20" fill={e.fill ? "currentColor" : "none"}
              stroke={e.fill ? "none" : "currentColor"} strokeWidth="1.4" strokeLinejoin="round">
              <path d={e.icon} />
            </svg>
          </span>
          <span className="ocl-elsewhere__label">{e.label}</span>
          <span className="ocl-elsewhere__value">{e.value}</span>
          <span className="ocl-elsewhere__note">{e.note}</span>
        </a>
      ))}
    </div>
  );
}

/** The corrections promise, with the little person who would rather know. */
export function AboutCorrections({ children }: { children: ReactNode }): ReactNode {
  const src = useBaseUrl("/img/art/steps/who-person.svg");
  return (
    <aside className="ocl-home__signoff ocl-corrections">
      <img className="ocl-home__doodle" src={src} alt="" aria-hidden="true" decoding="async" />
      <div>{children}</div>
    </aside>
  );
}
