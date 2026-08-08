"""
Modèle Camion : véhicules de collecte rattachés à une entreprise.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class StatutCamion(str, enum.Enum):
    actif = "actif"
    maintenance = "maintenance"
    inactif = "inactif"


class Camion(Base):
    __tablename__ = "camions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matricule = Column(String(30), nullable=False, unique=True)
    entreprise_id = Column(UUID(as_uuid=True), ForeignKey("entreprises_collecte.id"), nullable=False)
    statut = Column(Enum(StatutCamion), nullable=False, default=StatutCamion.actif)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)
