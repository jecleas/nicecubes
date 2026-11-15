CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE NOT NULL,
  cubes_created INTEGER NOT NULL DEFAULT 0,
  cubes_frozen INTEGER NOT NULL DEFAULT 0,
  trays_frozen INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Shared ice trays. active_cubes is a JSON array of cube indexes.
-- frozen_at and expires_at are ISO-8601 timestamps.
CREATE TABLE IF NOT EXISTS tray_state (
  id TEXT PRIMARY KEY,
  active_cubes TEXT NOT NULL DEFAULT '[]',
  is_frozen INTEGER NOT NULL DEFAULT 0,
  frozen_at TEXT,
  expires_at TEXT,
  revision INTEGER NOT NULL DEFAULT 0
);
