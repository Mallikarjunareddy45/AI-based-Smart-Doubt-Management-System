from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL should be fetched from environment variables, fallback for local dev
DATABASE_URL_ENV = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/ai_doubt_system"
)

def get_working_db_url(url: str) -> str:
    if not url:
        return url
        
    import re
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    
    # Standardize scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    # 1. Try URL as is
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect():
            return url
    except OperationalError:
        pass

    # 2. Try internal private URL (with sslmode stripped)
    url_no_ssl = url
    if "?" in url_no_ssl:
        base, query = url_no_ssl.split("?", 1)
        params = [p for p in query.split("&") if not p.startswith("sslmode=")]
        url_no_ssl = f"{base}?{'&'.join(params)}" if params else base
    try:
        engine = create_engine(url_no_ssl, connect_args={"connect_timeout": 3})
        with engine.connect():
            return url_no_ssl
    except OperationalError:
        pass

    # 3. Try public URL (replacing -a. with . and forcing sslmode=require)
    url_public = url
    if "-a." in url_public:
        url_public = re.sub(r'([-a-zA-Z0-9]+)-a\.(.*)\.render\.com', r'\1.\2.render.com', url_public)
    if "?" in url_public:
        base, query = url_public.split("?", 1)
        params = [p for p in query.split("&") if not p.startswith("sslmode=")]
        params.append("sslmode=require")
        url_public = f"{base}?{'&'.join(params)}"
    else:
        url_public = f"{url_public}?sslmode=require"
    try:
        engine = create_engine(url_public, connect_args={"connect_timeout": 3})
        with engine.connect():
            return url_public
    except OperationalError:
        pass

    # Fallback
    return url

DATABASE_URL = get_working_db_url(DATABASE_URL_ENV)

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
