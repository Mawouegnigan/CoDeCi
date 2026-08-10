"""
Routes pour les tournées (trajets) des chauffeurs.
"""
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

from app.models.bac_categorie import StatutBac
from app.schemas.trajet import CollecteReponse

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
from app.models.operations import TrajetCamion, StatutTrajet

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

@router.patch("/{trajet_id}/bacs/{bac_id}/collecter", response_model=CollecteReponse)
def collecter_bac(
    trajet_id: str,
    bac_id: str,
    utilisateur: Utilisateur = Depends(exiger_profil("chauffeur")),
    db: Session = Depends(get_db),
):
    """Marque un bac de la tournée comme collecté par le chauffeur connecté."""
    trajet = db.query(TrajetCamion).filter(TrajetCamion.id == trajet_id).first()

    if trajet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournée introuvable.",
        )

    if str(trajet.chauffeur_id) != str(utilisateur.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette tournée ne t'appartient pas.",
        )

    point_trouve = None
    for point in trajet.liste_points_gps:
        if point["bac_id"] == bac_id:
            point_trouve = point
            break

    if point_trouve is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ce bac ne fait pas partie de cette tournée.",
        )

    # Marque le point comme collecté dans le JSON (nécessite flag_modified
    # car SQLAlchemy ne détecte pas les mutations internes d'un JSONB).
    point_trouve["collecte"] = True
    point_trouve["heure_collecte"] = datetime.utcnow().isoformat()
    flag_modified(trajet, "liste_points_gps")

    # Met à jour le bac lui-même : vidé, avec horodatage.
    bac = db.query(BacPublic).filter(BacPublic.id == bac_id).first()
    if bac is not None:
        bac.statut = StatutBac.vide
        bac.derniere_vidange = datetime.utcnow()

    tous_collectes = all(p.get("collecte") for p in trajet.liste_points_gps)
    trajet.statut = StatutTrajet.termine if tous_collectes else StatutTrajet.en_cours

    db.commit()
    db.refresh(trajet)

    return CollecteReponse(
        bac_id=bac_id,
        statut_bac=bac.statut.value if bac else "inconnu",
        trajet_statut=trajet.statut,
        tous_bacs_collectes=tous_collectes,
    )