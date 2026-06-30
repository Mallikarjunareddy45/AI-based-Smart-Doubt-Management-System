from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL should be fetched from environment variables, fallback for local dev
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/ai_doubt_system"
)
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    import re
    DATABASE_URL = re.sub(r'([-a-zA-Z0-9]+)-a\.(.*)\.render\.com', r'\1.\2.render.com', DATABASE_URL)

# Create engine with connection pool configurations optimized for concurrency
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Auto-reconnect on dropped connections
    pool_size=20,            # Core connection pool size
    max_overflow=10,         # Maximum overflow connections under load
    pool_recycle=3600,       # Recycle connections hourly to prevent stale sockets
)

# Session factory for active DB connections
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
