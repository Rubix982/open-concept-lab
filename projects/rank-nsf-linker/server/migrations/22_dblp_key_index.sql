-- Collaborators on a profile join papers by their key: without this index every profile scanned
-- all ~885k paper rows (3.6 s).
CREATE INDEX IF NOT EXISTS dblp_papers_key_idx ON dblp_papers (dblp_key);
