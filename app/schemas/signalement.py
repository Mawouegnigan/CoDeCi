"""
Schémas Pydantic : définissent la forme des données échangées
via l'API (validation automatique des entrées/sorties).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SignalementReponse(BaseModel):
    id: uuid.UUID
    statut: str
    mode_soumission: str
    categorie_id: uuid.UUID
    commune_id: uuid.UUID
    date_creation: datetime
    photo_statut_verification: str
    motif_rejet: str | None = None

    class Config:
        from_attributes = True


class SignalementCreationEchec(BaseModel):
    detail: str
    motif: str = Field(description="Raison précise du rejet, utile pour l'app mobile")
