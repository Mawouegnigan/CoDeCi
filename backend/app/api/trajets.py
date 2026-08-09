"""
Routes pour les tournées (trajets) des chauffeurs.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.models.operations import TrajetCamion
from app.models.camion import Camion
from app.models.bac_categorie import BacPublic
from app.schemas.trajet import TrajetReponse, PointTrajetReponse
from app.api.dependencies import exiger_profil

router = APIRouter(prefix="/trajets", tags=["Trajets"])


@router.get("/aujourdhui", response_model=TrajetReponse)
def trajet_du_jour(
    utilisateur: Utilisateur = Depends(exiger_profil("chauffeur")),
    db: Session = Depends(get_db),
):
    """Renvoie la tournée du jour du chauffeur connecté, avec ses arrêts."""
    trajet = db.query(TrajetCamion).filter(
        TrajetCamion.chauffeur_id == utilisateur.id,
        TrajetCamion.date_trajet == date.today(),
    ).first()

    if trajet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune tournée planifiée pour aujourd'hui.",
        )

    camion = db.query(Camion).filter(Camion.id == trajet.camion_id).first()

    bac_ids = [point["bac_id"] for point in trajet.liste_points_gps]
    bacs = db.query(BacPublic).filter(BacPublic.id.in_(bac_ids)).all()
    bacs_par_id = {str(bac.id): bac for bac in bacs}

    points_tries = sorted(trajet.liste_points_gps, key=lambda p: p["ordre"])
    points = [
        PointTrajetReponse(
            bac_id=point["bac_id"],
            latitude=point["latitude"],
            longitude=point["longitude"],
            ordre=point["ordre"],
            statut_bac=(
                bacs_par_id[point["bac_id"]].statut.value
                if point["bac_id"] in bacs_par_id
                else None
            ),
        )
        for point in points_tries
    ]

    return TrajetReponse(
        id=trajet.id,
        date_trajet=trajet.date_trajet,
        statut=trajet.statut,
        camion_matricule=camion.matricule if camion else "N/A",
        points=points,
    )