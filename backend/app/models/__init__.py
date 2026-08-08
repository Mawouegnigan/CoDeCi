"""
Regroupe tous les modèles pour que SQLAlchemy les découvre correctement
au démarrage (nécessaire pour la création automatique des tables/migrations).
"""

from app.models.organisation import Commune, EntrepriseCollecte
from app.models.utilisateur import Utilisateur, ProfilUtilisateur
from app.models.camion import Camion, StatutCamion
from app.models.bac_categorie import BacPublic, StatutBac, CategorieSignalement
from app.models.photo import Photo, StatutVerificationPhoto
from app.models.signalement import Signalement, StatutSignalement, ModeSoumission
from app.models.operations import (
    TrajetCamion,
    StatutTrajet,
    PointSaute,
    TransactionPoints,
    TypeTransactionPoints,
)

__all__ = [
    "Commune",
    "EntrepriseCollecte",
    "Utilisateur",
    "ProfilUtilisateur",
    "Camion",
    "StatutCamion",
    "BacPublic",
    "StatutBac",
    "CategorieSignalement",
    "Photo",
    "StatutVerificationPhoto",
    "Signalement",
    "StatutSignalement",
    "ModeSoumission",
    "TrajetCamion",
    "StatutTrajet",
    "PointSaute",
    "TransactionPoints",
    "TypeTransactionPoints",
]
