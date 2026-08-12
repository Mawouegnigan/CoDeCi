"""
Schémas Pydantic pour la représentation des tournées (trajets) chauffeur.
"""
import uuid
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.models.operations import StatutTrajet


class PointTrajetReponse(BaseModel):
    """Un arrêt (bac) dans la tournée, avec son statut actuel."""
    bac_id: uuid.UUID
    latitude: float
    longitude: float
    ordre: int
    statut_bac: Optional[str] = None


class TrajetReponse(BaseModel):
    """Tournée du jour renvoyée au chauffeur, avec ses arrêts enrichis."""
    id: uuid.UUID
    date_trajet: date
    statut: StatutTrajet
    camion_matricule: str
    points: List[PointTrajetReponse]

    class Config:
        from_attributes = True

class CollecteReponse(BaseModel):
    """Confirmation après le marquage d'un bac comme collecté."""
    bac_id: uuid.UUID
    statut_bac: str
    trajet_statut: StatutTrajet
    tous_bacs_collectes: bool

class TrajetListeItem(BaseModel):
    """Un trajet dans la liste globale du dashboard, avec ses agrégats."""
    id: uuid.UUID
    date_trajet: date
    statut: StatutTrajet
    camion_matricule: str
    entreprise_nom: str
    chauffeur_nom: str
    nombre_bacs_total: int
    nombre_bacs_collectes: int


class TrajetListeReponse(BaseModel):
    """Réponse paginée pour la liste des trajets (vue dashboard)."""
    items: List[TrajetListeItem]
    total: int
    limit: int
    offset: int

class TrajetOptimiseReponse(BaseModel):
    """Tournée renvoyée après optimisation de l'ordre des bacs."""
    id: uuid.UUID
    points: List[PointTrajetReponse]
    class Config:
        from_attributes = True