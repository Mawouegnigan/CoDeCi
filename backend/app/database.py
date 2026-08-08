"""
Connexion à la base de données et gestion des sessions SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Fournit une session de base de données à chaque requête,
    et la ferme proprement après usage (pattern FastAPI standard).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
