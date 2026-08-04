"""
Modèles pour les entités organisationnelles et géographiques :
Communes et Entreprises de collecte.
"""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Commune(Base):
    __tablename__ = "communes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String(120), nullable=False)
    zone_geo = Column(Geography(geometry_type="POLYGON", srid=4326), nullable=False)

    # Opérateur de collecte attitré à cette commune (nullable : toutes
    # les communes du pays n'ont pas encore d'opérateur référencé).
    entreprise_collecte_id = Column(UUID(as_uuid=True), ForeignKey("entreprises_collecte.id"), nullable=True)

    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)

    entreprise_collecte = relationship("EntrepriseCollecte")


class EntrepriseCollecte(Base):
    __tablename__ = "entreprises_collecte"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String(150), nullable=False)
    zones_assignees = Column(Geography(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)
