"""
Modèles Bac public et Catégorie de signalement.
La catégorie est une table (pas un enum figé) pour rester
évolutive sans migration lourde si on ajoute des catégories plus tard.
"""

import uuid
import enum
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class StatutBac(str, enum.Enum):
    vide = "vide"
    moyen = "moyen"
    plein = "plein"


class BacPublic(Base):
    __tablename__ = "bacs_publics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    localisation = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    commune_id = Column(UUID(as_uuid=True), ForeignKey("communes.id"), nullable=False)
    statut = Column(Enum(StatutBac), nullable=False, default=StatutBac.moyen)
    derniere_vidange = Column(DateTime(timezone=True), nullable=True)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)


class CategorieSignalement(Base):
    __tablename__ = "categories_signalement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    libelle = Column(String(80), nullable=False, unique=True)
    description = Column(Text, nullable=True)
