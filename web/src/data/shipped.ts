// Tools that are deployed and in use, for /shipped. Each one also has its own page at
// src/pages/shipped/<name>.tsx; the smaller pages made in an afternoon stay on /built.

export type Shipped = {
  name: string; // the page is /shipped/<name>
  title: string;
  url: string; // where it runs
  what: string;
  since: string; // the day it went live, as written
  image: string; // under static/
};

export const SHIPPED: Shipped[] = [
  {
    name: "national-multi-care",
    title: "National Multi Care Hospital",
    url: "https://nmhnepalgunj.com/",
    what:
      "The website for a multi-specialty hospital in Nepalgunj, Nepal, in English, Nepali and Hindi. " +
      "Almost everyone who opens it arrives on a phone from a search result, often needing something " +
      "urgently, so the phone number, WhatsApp and the ambulance are in thumb reach on every page, and " +
      "the whole homepage weighs 200KB.",
    since: "16 September 2026",
    image: "/img/shipped/national-multi-care/home.jpg",
  },
  {
    name: "advisor-atlas",
    title: "Advisor Atlas",
    url: "https://advisoratlas.fyi/",
    what:
      "A map for finding a PhD advisor and a way to pay for the degree, made first for students in " +
      "Pakistan applying abroad. Say what you want to research in your own words; it finds the people " +
      "working on it, who funds them, the labs just starting out, and the scholarships you can apply for.",
    since: "11 October 2026",
    image: "/img/shipped/advisor-atlas/map.jpg",
  },
];
