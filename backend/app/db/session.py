from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL should be fetched from environment variables, fallback for local dev
DATABASE_URL_ENV = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/ai_doubt_system"
)

def get_normalized_db_url(url: str) -> str:
    if not url:
        return url
        
    import re
    # Standardize scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    # Convert internal Render database hostname to public hostname to allow SSL connections to succeed
    if "-a." in url:
        url = re.sub(r'([-a-zA-Z0-9]+)-a\.(.*)\.render\.com', r'\1.\2.render.com', url)
        
        # Ensure sslmode=require is present for the public connection
        if "?" in url:
            base, query = url.split("?", 1)
            params = [p for p in query.split("&") if not p.startswith("sslmode=")]
            params.append("sslmode=require")
            url = f"{base}?{'&'.join(params)}"
        else:
            url = f"{url}?sslmode=require"
            
    return url

DATABASE_URL = get_normalized_db_url(DATABASE_URL_ENV)

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
