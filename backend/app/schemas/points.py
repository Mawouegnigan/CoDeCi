"""
Schémas Pydantic pour le système de points citoyens et la conversion
en mobile money.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SoldeCitoyenReponse(BaseModel):
    solde_points: int


class ConversionReponse(BaseModel):
    id: uuid.UUID
    statut: str
    montant_points: int
    montant_fcfa: int | None = None
    reference_externe: str | None = None
    message: str

    class Config:
        from_attributes = True


class TransactionPointsItem(BaseModel):
    id: uuid.UUID
    type: str
    statut: str
    montant_points: int
    montant_fcfa: int | None = None
    reference_externe: str | None = None
    date_creation: datetime

    class Config:
        from_attributes = True


class TransactionPointsListeReponse(BaseModel):
    items: list[TransactionPointsItem]
    total: int