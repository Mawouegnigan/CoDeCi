"""
Service d'authentification : hashage des mots de passe et gestion des
tokens JWT. Isolé dans son propre service pour rester testable et
remplaçable (ex: bascule vers OTP par SMS en phase 2) sans toucher
aux routes ni aux modèles.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Hash un mot de passe en clair avec bcrypt. Ne jamais stocker le clair."""
    return _pwd_context.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Vérifie un mot de passe en clair contre son hash stocké en base."""
    return _pwd_context.verify(mot_de_passe, mot_de_passe_hash)


def creer_token_acces(utilisateur_id: str, profil: str) -> str:
    """
    Crée un JWT signé contenant l'id et le profil (rôle) de l'utilisateur.
    Le profil est inclus directement dans le token pour éviter une requête
    base de données supplémentaire à chaque vérification de permission.
    """
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expiration_minutes
    )
    payload = {
        "sub": str(utilisateur_id),
        "profil": profil,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decoder_token_acces(token: str) -> Optional[dict]:
    """Décode et valide un JWT. Retourne None si invalide ou expiré."""
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None