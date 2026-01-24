export type Faculty = {
  name: string; // part of the schema
  homepage?: string; // part of the schema
  matched_areas?: string[];
  interests?: string[];
  citations?: number;
  publications?: number;
  hindex?: number;
};

export type NSFAward = {
  title: string; // part of the schema, award_title_text
  amount: number; // part of the schema, award_amount
  years: number[]; // part of the schema, most_recent_amendment_date subtracted from earliest_amendment_date
};

export type UniStats = {
  active_awards?: number;
};

export type UniSummary = {
  institution: string; // part of schema
  longitude: number; // part of schema
  latitude: number; // part of schema
  top_area?: string; // for each university, get the faculty, get the distinct topic area for those faculty
  faculty_count?: number; // for each university, get the count of faculty
  funding?: number; // for each university, get the total funding, organize by year
  city?: string; // for each university, get their city
  region?: string; // for each university, get their region is populated
  country?: string; // for each university, get their country is populated
  faculty?: Faculty[]; // list of faculty with their details
  stats?: UniStats;
};

export type UniDetail = UniSummary & {
  city?: string; // part of schema
  country?: string; // part of schema
  homepage?: string; // part of schema
  faculty?: Faculty[]; // list of faculty with their details
  recent_nsf_awards?: NSFAward[]; // for each university, get recent NSF awards with details
};
