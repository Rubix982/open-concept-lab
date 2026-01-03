CREATE TABLE IF NOT EXISTS scraped_content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  professor_name TEXT NOT NULL,
  url TEXT NOT NULL,
  content_type TEXT, -- 'homepage', 'publication', 'project', 'bio'
  title TEXT,
  content TEXT,
  scraped_at TIMESTAMP DEFAULT NOW(),
  embedding_generated BOOLEAN DEFAULT FALSE,
  UNIQUE(professor_name, url)
);

CREATE INDEX IF NOT EXISTS idx_scraped_content_prof ON scraped_content(professor_name);
CREATE INDEX IF NOT EXISTS idx_scraped_content_emb ON scraped_content(embedding_generated);

CREATE TABLE IF NOT EXISTS scrape_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  professor_name TEXT NOT NULL,
  url TEXT NOT NULL,
  depth INTEGER DEFAULT 0,
  status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
  attempts INTEGER DEFAULT 0,
  last_attempt TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(professor_name, url)
);

CREATE INDEX IF NOT EXISTS idx_scrape_queue_status ON scrape_queue(status);

ALTER TABLE scrape_queue ADD COLUMN worker_id TEXT;

-- Prevent duplicate processing attempts
CREATE UNIQUE INDEX idx_processing_job ON scrape_queue(professor_name, url) WHERE status = 'processing';
