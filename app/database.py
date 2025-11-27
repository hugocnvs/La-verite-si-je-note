"""Initialisation de la base de données SQLModel/SQLAlchemy."""

from pathlib import Path
from typing import Generator

from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings


settings = get_settings()
database_url = settings.database_url
url = make_url(database_url)
connect_args = {"check_same_thread": False} if url.get_backend_name() == "sqlite" else {}

if url.database:
    db_path = Path(url.database)
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dépendance FastAPI pour ouvrir une session."""
    with Session(engine) as session:
        yield session

