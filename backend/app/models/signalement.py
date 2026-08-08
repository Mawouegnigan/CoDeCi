"""
Modèle Signalement : cœur du module citoyen.
"""

import uuid
import enum
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class StatutSignalement(str, enum.Enum):
    en_attente = "en_attente"
    en_cours = "en_cours"
    resolu = "resolu"
    rejete_fraude = "rejete_fraude"


class ModeSoumission(str, enum.Enum):
    en_ligne = "en_ligne"
    hors_ligne = "hors_ligne"


class Signalement(Base):
    __tablename__ = "signalements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    utilisateur_id = Column(UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False)
    categorie_id = Column(UUID(as_uuid=True), ForeignKey("categories_signalement.id"), nullable=False)
    bac_id = Column(UUID(as_uuid=True), ForeignKey("bacs_publics.id"), nullable=True)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id"), nullable=False)
    commune_id = Column(UUID(as_uuid=True), ForeignKey("communes.id"), nullable=False)

    coordonnees_gps = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    statut = Column(Enum(StatutSignalement), nullable=False, default=StatutSignalement.en_attente)
    mode_soumission = Column(Enum(ModeSoumission), nullable=False, default=ModeSoumission.en_ligne)

    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)
    date_resolution = Column(DateTime(timezone=True), nullable=True)

    photo = relationship("Photo")
    categorie = relationship("CategorieSignalement")
