"""
Routes d'authentification : inscription, connexion, et consultation
du profil de l'utilisateur actuellement connecté.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import (
    UtilisateurInscription,
    UtilisateurConnexion,
    UtilisateurReponse,
    TokenReponse,
)
from app.services.auth import (
    hasher_mot_de_passe,
    verifier_mot_de_passe,
    creer_token_acces,
)
from app.api.dependencies import get_utilisateur_courant

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/inscription", response_model=TokenReponse, status_code=status.HTTP_201_CREATED)
def inscription(donnees: UtilisateurInscription, db: Session = Depends(get_db)):
    """Crée un nouvel utilisateur (tout profil confondu) et renvoie un token."""
    telephone_existe = db.query(Utilisateur).filter(
        Utilisateur.telephone == donnees.telephone
    ).first()
    if telephone_existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce numéro de téléphone est déjà associé à un compte.",
        )

    utilisateur = Utilisateur(
        nom=donnees.nom,
        telephone=donnees.telephone,
        mot_de_passe_hash=hasher_mot_de_passe(donnees.mot_de_passe),
        profil=donnees.profil,
        commune_id=donnees.commune_id,
        entreprise_id=donnees.entreprise_id,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)

    token = creer_token_acces(utilisateur.id, utilisateur.profil.value)
    return TokenReponse(access_token=token, utilisateur=utilisateur)


@router.post("/connexion", response_model=TokenReponse)
def connexion(donnees: UtilisateurConnexion, db: Session = Depends(get_db)):
    """Vérifie téléphone + mot de passe, renvoie un token si valide."""
    erreur = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Numéro de téléphone ou mot de passe incorrect.",
    )

    utilisateur = db.query(Utilisateur).filter(
        Utilisateur.telephone == donnees.telephone
    ).first()

    if utilisateur is None or utilisateur.mot_de_passe_hash is None:
        raise erreur

    if not verifier_mot_de_passe(donnees.mot_de_passe, utilisateur.mot_de_passe_hash):
        raise erreur

    if not utilisateur.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été désactivé.",
        )

    token = creer_token_acces(utilisateur.id, utilisateur.profil.value)
    return TokenReponse(access_token=token, utilisateur=utilisateur)


@router.post("/connexion-swagger", include_in_schema=False)
def connexion_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Endpoint additionnel au format standard OAuth2 (username/password en
    form-data), requis uniquement pour que le bouton "Authorize" de la
    documentation Swagger (/docs) fonctionne. Le client Flutter doit
    utiliser /auth/connexion (JSON) et non celui-ci.
    """
    return connexion(
        UtilisateurConnexion(telephone=form_data.username, mot_de_passe=form_data.password),
        db,
    )


@router.get("/moi", response_model=UtilisateurReponse)
def profil_courant(utilisateur: Utilisateur = Depends(get_utilisateur_courant)):
    """Renvoie les infos de l'utilisateur actuellement authentifié."""
    return utilisateur