"""
Schémas Pydantic pour la représentation des bacs publics (vue dashboard).
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class BacListeItem(BaseModel):
    """Un bac public dans la liste globale du dashboard (pour la carte)."""
    id: uuid.UUID
    statut: str
    latitude: float
    longitude: float
    commune_nom: str
    derniere_vidange: Optional[datetime] = None


class BacListeReponse(BaseModel):
    """Réponse paginée pour la liste des bacs publics."""
    items: List[BacListeItem]
    total: int