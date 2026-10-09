-- CSRankings research areas: group -> area -> publication venue codes (professor_areas.area).
-- Rebuilt on every boot; the API serves it to the frontend.
CREATE TABLE IF NOT EXISTS research_area_venues (
  area_group TEXT NOT NULL,
  area TEXT NOT NULL,
  area_name TEXT NOT NULL,
  venue TEXT PRIMARY KEY
);
-- Only the CSRankings rows: the OpenAlex areas (venues 'oa:'/'oas:', added by later migrations and by
-- the pipeline from data/openalex/subfields.csv) stay. TRUNCATE dropped them on every boot, and a
-- server without data/openalex (a minimal deployment) then showed subfield codes ("sf1902") as areas.
DELETE FROM research_area_venues WHERE venue !~ '^oas?:';
INSERT INTO research_area_venues (area_group, area, area_name, venue) VALUES
  ('AI', 'ai', 'Artificial intelligence', 'aaai'),
  ('AI', 'ai', 'Artificial intelligence', 'ijcai'),
  ('AI', 'ml', 'Machine learning', 'mlmining'),
  ('AI', 'ml', 'Machine learning', 'icml'),
  ('AI', 'ml', 'Machine learning', 'kdd'),
  ('AI', 'ml', 'Machine learning', 'iclr'),
  ('AI', 'ml', 'Machine learning', 'nips'),
  ('AI', 'nlp', 'Natural language processing', 'nlp'),
  ('AI', 'nlp', 'Natural language processing', 'acl'),
  ('AI', 'nlp', 'Natural language processing', 'emnlp'),
  ('AI', 'nlp', 'Natural language processing', 'naacl'),
  ('AI', 'vision', 'Computer vision', 'vision'),
  ('AI', 'vision', 'Computer vision', 'cvpr'),
  ('AI', 'vision', 'Computer vision', 'eccv'),
  ('AI', 'vision', 'Computer vision', 'iccv'),
  ('AI', 'webir', 'The Web & information retrieval', 'inforet'),
  ('AI', 'webir', 'The Web & information retrieval', 'sigir'),
  ('AI', 'webir', 'The Web & information retrieval', 'www'),
  ('Systems', 'arch', 'Computer architecture', 'arch'),
  ('Systems', 'arch', 'Computer architecture', 'asplos'),
  ('Systems', 'arch', 'Computer architecture', 'isca'),
  ('Systems', 'arch', 'Computer architecture', 'micro'),
  ('Systems', 'arch', 'Computer architecture', 'hpca'),
  ('Systems', 'net', 'Computer networks', 'comm'),
  ('Systems', 'net', 'Computer networks', 'sigcomm'),
  ('Systems', 'net', 'Computer networks', 'nsdi'),
  ('Systems', 'sec', 'Computer security', 'sec'),
  ('Systems', 'sec', 'Computer security', 'ccs'),
  ('Systems', 'sec', 'Computer security', 'oakland'),
  ('Systems', 'sec', 'Computer security', 'usenixsec'),
  ('Systems', 'sec', 'Computer security', 'ndss'),
  ('Systems', 'sec', 'Computer security', 'pets'),
  ('Systems', 'db', 'Databases', 'mod'),
  ('Systems', 'db', 'Databases', 'sigmod'),
  ('Systems', 'db', 'Databases', 'vldb'),
  ('Systems', 'db', 'Databases', 'icde'),
  ('Systems', 'db', 'Databases', 'pods'),
  ('Systems', 'eda', 'Design automation', 'eda'),
  ('Systems', 'eda', 'Design automation', 'dac'),
  ('Systems', 'eda', 'Design automation', 'iccad'),
  ('Systems', 'emb', 'Embedded & real-time systems', 'bed'),
  ('Systems', 'emb', 'Embedded & real-time systems', 'emsoft'),
  ('Systems', 'emb', 'Embedded & real-time systems', 'rtas'),
  ('Systems', 'emb', 'Embedded & real-time systems', 'rtss'),
  ('Systems', 'hpc', 'High-performance computing', 'hpc'),
  ('Systems', 'hpc', 'High-performance computing', 'sc'),
  ('Systems', 'hpc', 'High-performance computing', 'hpdc'),
  ('Systems', 'hpc', 'High-performance computing', 'ics'),
  ('Systems', 'mobile', 'Mobile computing', 'mobile'),
  ('Systems', 'mobile', 'Mobile computing', 'mobicom'),
  ('Systems', 'mobile', 'Mobile computing', 'mobisys'),
  ('Systems', 'mobile', 'Mobile computing', 'sensys'),
  ('Systems', 'metrics', 'Measurement & perf. analysis', 'metrics'),
  ('Systems', 'metrics', 'Measurement & perf. analysis', 'imc'),
  ('Systems', 'metrics', 'Measurement & perf. analysis', 'sigmetrics'),
  ('Systems', 'os', 'Operating systems', 'ops'),
  ('Systems', 'os', 'Operating systems', 'sosp'),
  ('Systems', 'os', 'Operating systems', 'osdi'),
  ('Systems', 'os', 'Operating systems', 'fast'),
  ('Systems', 'os', 'Operating systems', 'usenixatc'),
  ('Systems', 'os', 'Operating systems', 'eurosys'),
  ('Systems', 'pl', 'Programming languages', 'pldi'),
  ('Systems', 'pl', 'Programming languages', 'popl'),
  ('Systems', 'pl', 'Programming languages', 'icfp'),
  ('Systems', 'pl', 'Programming languages', 'oopsla'),
  ('Systems', 'pl', 'Programming languages', 'plan'),
  ('Systems', 'se', 'Software engineering', 'soft'),
  ('Systems', 'se', 'Software engineering', 'fse'),
  ('Systems', 'se', 'Software engineering', 'icse'),
  ('Systems', 'se', 'Software engineering', 'ase'),
  ('Systems', 'se', 'Software engineering', 'issta'),
  ('Theory', 'theory', 'Algorithms & complexity', 'act'),
  ('Theory', 'theory', 'Algorithms & complexity', 'focs'),
  ('Theory', 'theory', 'Algorithms & complexity', 'soda'),
  ('Theory', 'theory', 'Algorithms & complexity', 'stoc'),
  ('Theory', 'crypto', 'Cryptography', 'crypt'),
  ('Theory', 'crypto', 'Cryptography', 'crypto'),
  ('Theory', 'crypto', 'Cryptography', 'eurocrypt'),
  ('Theory', 'log', 'Logic & verification', 'log'),
  ('Theory', 'log', 'Logic & verification', 'cav'),
  ('Theory', 'log', 'Logic & verification', 'lics'),
  ('Interdisciplinary', 'comp-bio', 'Comp. bio & bioinformatics', 'bio'),
  ('Interdisciplinary', 'comp-bio', 'Comp. bio & bioinformatics', 'ismb'),
  ('Interdisciplinary', 'comp-bio', 'Comp. bio & bioinformatics', 'recomb'),
  ('Interdisciplinary', 'graphics', 'Computer graphics', 'graph'),
  ('Interdisciplinary', 'graphics', 'Computer graphics', 'siggraph'),
  ('Interdisciplinary', 'graphics', 'Computer graphics', 'siggraph-asia'),
  ('Interdisciplinary', 'graphics', 'Computer graphics', 'eurographics'),
  ('Interdisciplinary', 'csed', 'Computer science education', 'csed'),
  ('Interdisciplinary', 'csed', 'Computer science education', 'sigcse'),
  ('Interdisciplinary', 'ecom', 'Economics & computation', 'ecom'),
  ('Interdisciplinary', 'ecom', 'Economics & computation', 'ec'),
  ('Interdisciplinary', 'ecom', 'Economics & computation', 'wine'),
  ('Interdisciplinary', 'hci', 'Human-computer interaction', 'chi'),
  ('Interdisciplinary', 'hci', 'Human-computer interaction', 'chiconf'),
  ('Interdisciplinary', 'hci', 'Human-computer interaction', 'ubicomp'),
  ('Interdisciplinary', 'hci', 'Human-computer interaction', 'uist'),
  ('Interdisciplinary', 'robotics', 'Robotics', 'robotics'),
  ('Interdisciplinary', 'robotics', 'Robotics', 'icra'),
  ('Interdisciplinary', 'robotics', 'Robotics', 'iros'),
  ('Interdisciplinary', 'robotics', 'Robotics', 'rss'),
  ('Interdisciplinary', 'visualization', 'Visualization', 'visualization'),
  ('Interdisciplinary', 'visualization', 'Visualization', 'vis'),
  ('Interdisciplinary', 'visualization', 'Visualization', 'vr');

-- Precomputed tables the explorer API reads (rebuilt by the "Build Explorer Tables" step).
CREATE TABLE IF NOT EXISTS explorer_faculty (
  name TEXT PRIMARY KEY,
  university TEXT NOT NULL,
  homepage TEXT,
  scholar_id TEXT,
  areas TEXT[] NOT NULL,          -- areas with publications in the last 10 years
  area_pubs JSONB NOT NULL,       -- area -> papers at the area's top venues, last 10 years
  recent_pubs REAL NOT NULL,
  active_awards INTEGER NOT NULL,
  total_awards INTEGER NOT NULL,
  active_funding BIGINT NOT NULL,
  last_award_date DATE
);
CREATE INDEX IF NOT EXISTS explorer_faculty_university_idx ON explorer_faculty (university);
CREATE INDEX IF NOT EXISTS explorer_faculty_areas_idx ON explorer_faculty USING gin (areas);

-- One searchable document per piece of a professor's work: an NSF award (title A + abstract B)
-- or a recent paper (title A). Goal matching ranks a professor by their single best match.
CREATE TABLE IF NOT EXISTS explorer_work_docs (
  name TEXT NOT NULL,
  kind TEXT NOT NULL,             -- 'award' | 'paper'
  ref TEXT NOT NULL,              -- NSF award id | DBLP key
  title TEXT,
  year INTEGER,
  url TEXT,
  doc TSVECTOR NOT NULL,
  PRIMARY KEY (name, kind, ref)
);
CREATE INDEX IF NOT EXISTS explorer_work_docs_doc_idx ON explorer_work_docs USING gin (doc);
DROP TABLE IF EXISTS explorer_award_docs;

CREATE TABLE IF NOT EXISTS explorer_universities (
  id TEXT PRIMARY KEY,            -- institution_key, stable across rebuilds
  name TEXT NOT NULL UNIQUE,
  city TEXT,
  state TEXT,
  country TEXT,
  latitude REAL,
  longitude REAL,
  homepage TEXT,
  carnegie TEXT,                  -- 'R1' / 'R2' / NULL
  grad_tuition_in_state INTEGER,
  grad_tuition_out_of_state INTEGER,
  grad_enrollment INTEGER,
  faculty_count INTEGER NOT NULL,
  funded_faculty INTEGER NOT NULL,  -- faculty with an active NSF award
  area_faculty JSONB NOT NULL,      -- area -> faculty count
  area_funded JSONB NOT NULL        -- area -> faculty with an active NSF award
);

-- Recent publications of CSRankings faculty, from the DBLP XML dump ("Load DBLP Papers" step).
-- DBLP and CSRankings share person names ("Wei Wang 0001").
CREATE TABLE IF NOT EXISTS dblp_papers (
  name TEXT NOT NULL,
  dblp_key TEXT NOT NULL,
  title TEXT NOT NULL,
  venue TEXT,
  year INTEGER NOT NULL,
  url TEXT,
  PRIMARY KEY (name, dblp_key)
);
DROP TABLE IF EXISTS dblp_cache;

-- Points held in the Qdrant collection explorer_work (semantic goal matching), with a hash of
-- each point's payload so the "Embed Explorer Work" step only re-embeds or re-labels what changed.
CREATE TABLE IF NOT EXISTS explorer_embedded (
  id UUID PRIMARY KEY,
  payload_hash TEXT NOT NULL
);
