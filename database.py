# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path

# Must match the container volume mount unless overridden by deployment config.
DATABASE_PATH = os.getenv("DATABASE_PATH") or os.path.join(os.getenv("DB_PATH", "/app/data"), "app.db")
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATABASE_PATH}"

if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if sqlite_path and sqlite_path != ":memory:":
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


