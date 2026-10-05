// Client for the explorer API (server/explorer_api.go). nginx and the Vite dev server
// proxy /api to the Go server.

export type Area = {
  group: string;
  area: string;
  name: string;
  faculty: number;
  funded: number;
};

export type UniversitySummary = {
  id: string;
  name: string;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  carnegie: "R1" | "R2" | null;
  faculty_total: number;
  funded_total: number;
  faculty: number; // in the selected areas
  funded: number; // in the selected areas, with an active NSF grant
  goal_matches: number;
};

export type UniversityDetail = UniversitySummary & {
  homepage?: string;
  grad_tuition_in_state?: number;
  grad_tuition_out_of_state?: number;
  grad_enrollment?: number;
  area_faculty: Record<string, number>;
  area_funded: Record<string, number>;
  grant_funders?: string[];
  doctoral_degrees?: number; // IPEDS, all fields, latest year (US)
  doctoral_year?: number;
  funders?: { funder: string; people: number; active_people: number }[];
  recently_funded?: {
    name: string;
    funder: string;
    title: string;
    year: number;
  }[];
};

export type Work = {
  funder?: string;
  kind: "award" | "paper";
  title: string;
  year: number | null;
  url: string | null;
};

export type Faculty = {
  name: string;
  source?: "csrankings" | "openalex"; // openalex: a researcher in another field, not verified faculty
  university: string;
  university_id: string | null;
  country: string | null;
  homepage: string | null;
  scholar_id: string | null;
  areas: string[];
  area_pubs: Record<string, number>;
  recent_pubs: number;
  active_awards: number;
  total_awards: number;
  active_funding: number;
  last_award_date: string | null;
  funding: FundingEntry[] | null;
  goal_score?: number;
  match?: Work;
  latest_work?: {
    title: string;
    year: number | null;
    url: string | null;
  } | null;
  first_year?: number | null; // first top-venue paper (CSRankings faculty)
  orcid?: string | null;
  openalex_id?: string | null;
};

export type FundingEntry = {
  funder: string;
  currency: string;
  active: number;
  lead_active?: number; // active grants this person leads
  total: number;
  active_amount: number; // of the active grants they lead
};

export type Funders = {
  names: Record<string, string>;
  by_country: Record<string, string[]>;
};

export type Award = {
  id: string;
  funder: string;
  currency: string;
  title: string;
  amount: number;
  starts: string | null;
  ends: string | null;
  active: boolean;
  role: string | null;
  abstract: string;
  url: string;
  institution?: string; // where the grant is held
  lead?: boolean; // this person leads it
  team?: { name: string; role: string; profile: string | null }[];
};

export type Collaborator = { name: string; university: string; papers: number };
export type SimilarPerson = {
  name: string;
  university: string;
  score: number;
  source: string;
};

export type Paper = {
  title: string;
  venue: string | null;
  year: number;
  url: string | null;
  match?: boolean; // close to the student's goal (only when a goal was given)
  snippet?: string | null; // start of the abstract (OpenAlex)
  topic?: string | null;
  cited_by?: number | null;
};

export type GrantPerson = {
  name: string;
  university: string;
  university_id: string | null;
};

export type Grant = Award & { similarity: number; people: GrantPerson[] };

export type Scholarship = {
  id: string;
  name: string;
  provider: string;
  destinations: string[];
  levels: string[];
  eligible_nationalities: string[];
  covers: string;
  application_window: string;
  url: string;
  verified: boolean;
  notes: string;
  eligibility: "eligible" | "check";
  source: string; // "curated", or a feed ("daad")
};

export type Query = { areas: string[]; goal: string };

// Where money for a search goes, across every grant loaded (linked to someone on the map or not).
export type Landscape = {
  total: number;
  active: number;
  funders: {
    funder: string;
    currency: string | null;
    grants: number;
    active: number;
    amount: number | null;
    active_amount: number | null;
  }[];
  years: { year: number; funder: string; grants: number }[];
  places: {
    institution: string;
    university_id: string | null;
    country: string | null;
    grants: number;
    active: number;
    people: number;
  }[];
  grants: {
    funder: string;
    id: string;
    title: string;
    snippet: string | null;
    amount: number | null;
    currency: string | null;
    starts: string | null;
    ends: string | null;
    url: string | null;
    lead: string | null;
    institution: string | null;
    university_id: string | null;
    profile: string | null;
  }[];
};

function params(q: Partial<Query> & Record<string, unknown>): string {
  const p = new URLSearchParams();
  if (q.areas?.length) p.set("areas", q.areas.join(","));
  if (q.goal?.trim()) p.set("q", q.goal.trim());
  for (const [k, v] of Object.entries(q)) {
    if (k !== "areas" && k !== "goal" && v !== undefined && v !== "")
      p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`/api/explorer${path}`, { signal });
  if (res.status === 503) {
    throw new Error(
      "The data is still loading on the server. Try again in a few minutes.",
    );
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  landscape: (
    q: { goal: string; active?: boolean; country?: string },
    signal?: AbortSignal,
  ) =>
    get<Landscape>(
      `/landscape?q=${encodeURIComponent(q.goal)}${q.active ? "&active=1" : ""}${q.country ? `&country=${q.country}` : ""}`,
      signal,
    ),
  areas: () => get<Area[]>("/areas"),
  funders: () => get<Funders>("/funders"),
  universities: (q: Query, signal?: AbortSignal) =>
    get<UniversitySummary[]>(`/universities${params(q)}`, signal),
  university: (id: string) =>
    get<UniversityDetail>(`/universities/${encodeURIComponent(id)}`),
  faculty: (
    q: Query & { university?: string; limit?: number },
    signal?: AbortSignal,
  ) => get<Faculty[]>(`/faculty${params(q)}`, signal),
  profile: (name: string) =>
    get<{
      faculty: Faculty;
      awards: Award[];
      collaborators: Collaborator[];
      previously: string[];
      topics: { topic: string; papers: number }[];
    }>(`/faculty/profile?name=${encodeURIComponent(name)}`),
  similar: (name: string) =>
    get<{ similar: SimilarPerson[] }>(
      `/faculty/similar?name=${encodeURIComponent(name)}`,
    ),
  grants: (
    q: Query & { active: boolean; limit?: number },
    signal?: AbortSignal,
  ) =>
    get<Grant[]>(
      `/grants${params({ ...q, active: q.active ? 1 : 0 })}`,
      signal,
    ),
  scholarships: (country: string) =>
    get<Scholarship[]>(`/scholarships?country=${encodeURIComponent(country)}`),
  papers: (name: string, goal = "") =>
    get<{ dblp_url: string; papers: Paper[] }>(
      `/faculty/papers?name=${encodeURIComponent(name)}${goal ? `&goal=${encodeURIComponent(goal)}` : ""}`,
    ),
};
