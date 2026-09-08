"""
Modèles pour la partie opérationnelle : trajets des chauffeurs,
alertes de points sautés, et transactions du programme de points.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class StatutTrajet(str, enum.Enum):
    planifie = "planifie"
    en_cours = "en_cours"
    termine = "termine"


class TrajetCamion(Base):
    __tablename__ = "trajets_camions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chauffeur_id = Column(UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camions.id"), nullable=False)

    # Liste ordonnée des points GPS à parcourir (calculée par le module d'optimisation)
    liste_points_gps = Column(JSONB, nullable=False)
    ordre_modifie_manuellement = Column(Boolean, nullable=False, default=False)

    date_trajet = Column(Date, nullable=False)
    statut = Column(Enum(StatutTrajet), nullable=False, default=StatutTrajet.planifie)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)


class PointSaute(Base):
    __tablename__ = "points_sautes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trajet_id = Column(UUID(as_uuid=True), ForeignKey("trajets_camions.id"), nullable=False)
    bac_id = Column(UUID(as_uuid=True), ForeignKey("bacs_publics.id"), nullable=False)
    chauffeur_id = Column(UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False)
    alerte_envoyee = Column(Boolean, nullable=False, default=False)
    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)


class TypeTransactionPoints(str, enum.Enum):
    gain_signalement = "gain_signalement"
    gain_tri_selectif = "gain_tri_selectif"
    conversion_mobile_money = "conversion_mobile_money"
    annulation_conversion = "annulation_conversion"


class StatutTransactionPoints(str, enum.Enum):
    en_attente = "en_attente"
    reussi = "reussi"
    echoue = "echoue"


class TransactionPoints(Base):
    """
    Registre de points citoyens (ledger en partie double). Source de
    vérité auditable : Utilisateur.solde_points est un champ de cache
    mis à jour à chaque écriture ici, jamais modifié directement.

    signalement_id est unique en base : garantit qu'un même signalement
    ne peut jamais être crédité deux fois (idempotence).
    """
    __tablename__ = "transactions_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utilisateur_id = Column(UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False)
    signalement_id = Column(UUID(as_uuid=True), ForeignKey("signalements.id"), nullable=True, unique=True)

    montant_points = Column(Integer, nullable=False)
    type = Column(Enum(TypeTransactionPoints), nullable=False)
    statut = Column(Enum(StatutTransactionPoints), nullable=False, default=StatutTransactionPoints.reussi)

    # Renseignés uniquement pour les débits (conversion MoMo, chantier 3).
    montant_fcfa = Column(Integer, nullable=True)
    numero_telephone = Column(String(20), nullable=True)
    reference_externe = Column(String(100), nullable=True)

    date_creation = Column(DateTime(timezone=True), default=datetime.utcnow)
    date_maj = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)