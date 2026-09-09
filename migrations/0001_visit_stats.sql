CREATE TABLE IF NOT EXISTS visitors (
  id TEXT PRIMARY KEY,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS counters (
  key TEXT PRIMARY KEY,
  value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS daily_views (
  day TEXT PRIMARY KEY,
  value INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_visitors_last_seen ON visitors(last_seen);
