-- CSRankings lists some people under several names ("Dylan A. Shell" / "Dylan Shell"). The explorer
-- shows one person per group; this maps every name to the group's main name ("Build Explorer Tables").
CREATE TABLE IF NOT EXISTS professor_variants (
  name TEXT PRIMARY KEY,
  canonical TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS professor_variants_canonical_idx ON professor_variants (canonical);

-- Current and former affiliations of CSRankings people, from DBLP person records ("Load DBLP Papers").
-- Evidence for linking NSF investigators who moved universities after CSRankings recorded them.
CREATE TABLE IF NOT EXISTS dblp_affiliations (
  name TEXT NOT NULL,           -- CSRankings name (one row per name spelling DBLP lists)
  affiliation TEXT NOT NULL,    -- "Michigan State University, East Lansing, MI, USA"
  former BOOLEAN NOT NULL
);
CREATE INDEX IF NOT EXISTS dblp_affiliations_name_idx ON dblp_affiliations (name);
