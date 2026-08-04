"""
Modèle Utilisateur : couvre tous les profils (citoyen, chauffeur,
agent municipal, entreprise, admin, ministère) via un champ "profil".
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProfilUtilisateur(str, enum.Enum):
    citoyen = "citoyen"
    chauffeur = "chauffeur"
    agent_municipal = "agent_municipal"
    entreprise = "entreprise"
    admin = "admin"
    ministere = "ministere"


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String(150), nullable=False)
    telephone = Column(String(20), nullable=False, unique=True, index=True)
    profil = Column(Enum(ProfilUtilisateur), nullable=False, index=True)

    commune_id = Column(UUID(as_uuid=True), ForeignKey("communes.id"), nullable=True)
    entreprise_id = Column(UUID(as_uuid=True), ForeignKey("entreprises_collecte.id"), nullable=True)

    solde_points = Column(Integer, nullable=False, default=0)
    actif = Column(Boolean, nullable=False, default=True)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)

    commune = relationship("Commune")
    entreprise = relationship("EntrepriseCollecte")
