"""
Routes pour la consultation des bacs publics (vue dashboard / carte).
"""
from geoalchemy2.shape import to_shape
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.models.bac_categorie import BacPublic
from app.models.organisation import Commune
from app.schemas.bac import BacListeItem, BacListeReponse
from app.api.dependencies import exiger_profil

router = APIRouter(prefix="/bacs", tags=["Bacs"])


@router.get("", response_model=BacListeReponse)
def lister_bacs(
    utilisateur: Utilisateur = Depends(
        exiger_profil("agent_municipal", "entreprise", "admin", "ministere")
    ),
    db: Session = Depends(get_db),
):
    """
    Liste tous les bacs publics avec leur position et statut, pour
    affichage sur la carte du dashboard. Lecture seule, pas de pagination
    (volume attendu limité à quelques centaines de bacs pour le MVP).

    Scoping par profil :
    - agent_municipal : ne voit que les bacs de sa propre commune.
    - entreprise, admin, ministere : accès complet (une entreprise de
      collecte doit voir tous les bacs pour planifier ses tournées,
      pas seulement ceux d'une commune).
    """
    requete = db.query(BacPublic)

    if utilisateur.profil == "agent_municipal":
        if utilisateur.commune_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ce compte n'est rattaché à aucune commune.",
            )
        requete = requete.filter(BacPublic.commune_id == utilisateur.commune_id)

    bacs = requete.all()

    items = []
    for bac in bacs:
        point = to_shape(bac.localisation)
        commune = db.query(Commune).filter(Commune.id == bac.commune_id).first()

        items.append(BacListeItem(
            id=bac.id,
            statut=bac.statut.value,
            latitude=point.y,
            longitude=point.x,
            commune_nom=commune.nom if commune else "N/A",
            derniere_vidange=bac.derniere_vidange,
        ))

    return BacListeReponse(items=items, total=len(items))