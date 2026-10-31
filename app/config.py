"""All configuration comes from environment variables (12-factor style)."""
import os

# Docker Compose passes a PostgreSQL URL; without it the API falls back to a local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bounty.db")

# Fill an empty database with the sample data (8 criminals, 14 hunt logs) on startup.
AUTO_SEED = os.getenv("AUTO_SEED", "true").strip().lower() in {"1", "true", "yes", "on"}
