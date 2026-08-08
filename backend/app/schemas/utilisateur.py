"""
Schémas Pydantic pour l'authentification et la représentation des
utilisateurs dans les réponses API.
"""
import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.utilisateur import ProfilUtilisateur


class UtilisateurInscription(BaseModel):
    """Données requises pour créer un compte."""
    nom: str = Field(min_length=2, max_length=150)
    telephone: str = Field(min_length=8, max_length=20)
    mot_de_passe: str = Field(min_length=8, max_length=72)
    profil: ProfilUtilisateur
    commune_id: Optional[uuid.UUID] = None
    entreprise_id: Optional[uuid.UUID] = None

    @field_validator("telephone")
    @classmethod
    def nettoyer_telephone(cls, valeur: str) -> str:
        # Retire espaces et tirets courants dans la saisie d'un numéro ivoirien.
        return valeur.replace(" ", "").replace("-", "")


class UtilisateurConnexion(BaseModel):
    """Données requises pour se connecter."""
    telephone: str
    mot_de_passe: str


class UtilisateurReponse(BaseModel):
    """Représentation d'un utilisateur renvoyée par l'API (jamais le mot de passe)."""
    id: uuid.UUID
    nom: str
    telephone: str
    profil: ProfilUtilisateur
    commune_id: Optional[uuid.UUID] = None
    entreprise_id: Optional[uuid.UUID] = None
    solde_points: int
    actif: bool

    class Config:
        from_attributes = True


class TokenReponse(BaseModel):
    """Réponse renvoyée après une connexion ou une inscription réussie."""
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurReponse