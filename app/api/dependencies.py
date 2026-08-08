"""
Dépendances FastAPI réutilisables pour protéger les routes :
- get_utilisateur_courant : exige un token JWT valide
- exiger_profil(...) : exige en plus un ou plusieurs rôles précis

Utilisation dans une route :
    @router.get("/dashboard/admin")
    def route_admin(utilisateur: Utilisateur = Depends(exiger_profil("admin"))):
        ...
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.utilisateur import Utilisateur, ProfilUtilisateur
from app.services.auth import decoder_token_acces

# tokenUrl pointe vers la route de connexion compatible OAuth2 (form-data),
# utilisée par la doc Swagger (/docs) pour afficher le bouton "Authorize".
# ATTENTION : ce n'est PAS la route utilisée par le client Flutter
# (qui utilise /auth/connexion, en JSON).
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/connexion-swagger")


def get_utilisateur_courant(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilisateur:
    """Résout l'utilisateur associé au token JWT fourni. Lève 401 si invalide."""
    erreur_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decoder_token_acces(token)
    if payload is None:
        raise erreur_auth

    utilisateur_id = payload.get("sub")
    if utilisateur_id is None:
        raise erreur_auth

    utilisateur = db.query(Utilisateur).filter(
        Utilisateur.id == uuid.UUID(utilisateur_id)
    ).first()

    if utilisateur is None or not utilisateur.actif:
        raise erreur_auth

    return utilisateur


def exiger_profil(*profils_autorises: ProfilUtilisateur):
    """
    Fabrique une dépendance qui exige que l'utilisateur connecté ait
    l'un des profils passés en argument. Réutilisable sur toutes les
    futures routes chauffeur / dashboard / admin.
    """
    def verificateur(
        utilisateur: Utilisateur = Depends(get_utilisateur_courant),
    ) -> Utilisateur:
        if utilisateur.profil not in profils_autorises:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce profil utilisateur.",
            )
        return utilisateur

    return verificateur