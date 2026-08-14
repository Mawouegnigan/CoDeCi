"""
Routes pour les tournées (trajets) des chauffeurs.
"""
from app.models.operations import TrajetCamion, StatutTrajet
from typing import Optional
from app.models.organisation import EntrepriseCollecte
from app.schemas.trajet import TrajetListeItem, TrajetListeReponse
import uuid
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

from app.models.bac_categorie import StatutBac
from app.models.operations import PointSaute
from app.schemas.trajet import CollecteReponse
from app.models.bac_categorie import BacPublic

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

from app.schemas.trajet import TrajetOptimiseReponse
from app.services.optimisation import optimiser_tournee, ErreurOptimisation
from app.services.alertes import envoyer_alerte_point_saute

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


def _detecter_points_sautes(
    trajet: TrajetCamion,
    bac_collecte_id: str,
    ordre_collecte,
    chauffeur_id,
    db: Session,
) -> list[PointSaute]:
    """
    Après qu'un bac soit marqué collecté, vérifie si des bacs plus tôt
    dans l'ordre planifié de la tournée n'ont pas encore été collectés.
    Chacun constitue un point sauté : le chauffeur est passé devant sans
    le vider, dans le désordre de la tournée prévue.

    Idempotent : ne crée pas de doublon si ce bac a déjà été flaggé comme
    sauté sur ce trajet lors d'un appel précédent. Renvoie la liste des
    nouveaux objets PointSaute créés lors de cet appel (pas encore
    committés), pour permettre l'envoi d'alertes email juste après.
    """
    ids_deja_flagges = {
        str(row.bac_id)
        for row in db.query(PointSaute.bac_id)
        .filter(PointSaute.trajet_id == trajet.id)
        .all()
    }

    nouveaux = []
    for point in trajet.liste_points_gps:
        if point["bac_id"] == bac_collecte_id:
            continue
        if point["ordre"] >= ordre_collecte:
            continue
        if point.get("collecte"):
            continue
        if point["bac_id"] in ids_deja_flagges:
            continue  # déjà tracé lors d'un passage précédent

        point_saute = PointSaute(
            trajet_id=trajet.id,
            bac_id=uuid.UUID(point["bac_id"]),
            chauffeur_id=chauffeur_id,
        )
        db.add(point_saute)
        nouveaux.append(point_saute)

    return nouveaux



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

    nouveaux_points_sautes = _detecter_points_sautes(
        trajet=trajet,
        bac_collecte_id=bac_id,
        ordre_collecte=point_trouve["ordre"],
        chauffeur_id=utilisateur.id,
        db=db,
    )

    point_trouve["collecte"] = True
    point_trouve["heure_collecte"] = datetime.utcnow().isoformat()
    flag_modified(trajet, "liste_points_gps")

    bac = db.query(BacPublic).filter(BacPublic.id == bac_id).first()
    if bac is not None:
        bac.statut = StatutBac.vide
        bac.derniere_vidange = datetime.utcnow()

    tous_collectes = all(p.get("collecte") for p in trajet.liste_points_gps)
    trajet.statut = StatutTrajet.termine if tous_collectes else StatutTrajet.en_cours

    db.commit()
    db.refresh(trajet)

    # Envoi des alertes email pour les nouveaux points sautés détectés.
    # Effectué après le commit principal pour ne jamais bloquer la
    # collecte du chauffeur en cas de souci SMTP.
    if nouveaux_points_sautes:
        camion = db.query(Camion).filter(Camion.id == trajet.camion_id).first()
        entreprise = (
            db.query(EntrepriseCollecte).filter(EntrepriseCollecte.id == camion.entreprise_id).first()
            if camion else None
        )
        chauffeur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur.id).first()

        if entreprise is not None and entreprise.email_contact:
            for point_saute in nouveaux_points_sautes:
                envoye = envoyer_alerte_point_saute(
                    email_destinataire=entreprise.email_contact,
                    entreprise_nom=entreprise.nom,
                    camion_matricule=camion.matricule if camion else "N/A",
                    chauffeur_nom=chauffeur.nom if chauffeur else "N/A",
                    bac_id=str(point_saute.bac_id),
                    date_trajet=str(trajet.date_trajet),
                )
                point_saute.alerte_envoyee = envoye
            db.commit()

    return CollecteReponse(
        bac_id=bac_id,
        statut_bac=bac.statut.value if bac else "inconnu",
        trajet_statut=trajet.statut,
        tous_bacs_collectes=tous_collectes,
    )


@router.post("/{trajet_id}/optimiser", response_model=TrajetOptimiseReponse)
def optimiser_trajet(
    trajet_id: str,
    utilisateur: Utilisateur = Depends(
        exiger_profil("agent_municipal", "entreprise", "admin", "ministere")
    ),
    db: Session = Depends(get_db),
):
    """Recalcule l'ordre optimal des bacs d'une tournée via OR-Tools + Mapbox."""
    trajet = db.query(TrajetCamion).filter(TrajetCamion.id == trajet_id).first()

    if trajet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournée introuvable.",
        )

    if utilisateur.profil == "entreprise":
        camion = db.query(Camion).filter(Camion.id == trajet.camion_id).first()
        if camion is None or str(camion.entreprise_id) != str(utilisateur.entreprise_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cette tournée n'appartient pas à votre entreprise.",
            )

    if len(trajet.liste_points_gps) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pas assez de points dans cette tournée pour optimiser l'ordre.",
        )

    try:
        points_optimises = optimiser_tournee(trajet.liste_points_gps)
    except ErreurOptimisation as erreur:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(erreur),
        )

    trajet.liste_points_gps = points_optimises
    trajet.ordre_modifie_manuellement = False
    flag_modified(trajet, "liste_points_gps")
    db.commit()
    db.refresh(trajet)

    points_reponse = [
        PointTrajetReponse(
            bac_id=p["bac_id"],
            latitude=p["latitude"],
            longitude=p["longitude"],
            ordre=p["ordre"],
            statut_bac=None,
        )
        for p in trajet.liste_points_gps
    ]

    return TrajetOptimiseReponse(id=trajet.id, points=points_reponse)


@router.get("", response_model=TrajetListeReponse)
def lister_trajets(
    date_trajet: Optional[date] = None,
    statut: Optional[StatutTrajet] = None,
    entreprise_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
    utilisateur: Utilisateur = Depends(
        exiger_profil("agent_municipal", "entreprise", "admin", "ministere")
    ),
    db: Session = Depends(get_db),
):
    """
    Liste les tournées pour les tableaux de bord. Par défaut, ne montre
    que les tournées du jour ; passer date_trajet pour consulter un autre
    jour. Lecture seule, triée par statut puis heure de création.

    Scoping par profil :
    - entreprise : ne voit que les tournées de ses propres camions
      (entreprise_id en paramètre est ignoré si présent).
    - admin / ministere : accès complet, entreprise_id optionnel comme filtre.
    - agent_municipal : accès complet pour l'instant (scoping par commune
      à ajouter séparément, pas de lien direct commune↔trajet en base).
    """
    if limit < 1 or limit > 200:
        limit = 50
    if offset < 0:
        offset = 0

    date_filtree = date_trajet or date.today()

    requete = (
        db.query(TrajetCamion)
        .join(Camion, TrajetCamion.camion_id == Camion.id)
        .filter(TrajetCamion.date_trajet == date_filtree)
    )

    if statut is not None:
        requete = requete.filter(TrajetCamion.statut == statut)

    if utilisateur.profil == "entreprise":
        if utilisateur.entreprise_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ce compte n'est rattaché à aucune entreprise.",
            )
        requete = requete.filter(Camion.entreprise_id == utilisateur.entreprise_id)
    elif entreprise_id is not None:
        requete = requete.filter(Camion.entreprise_id == entreprise_id)

    trajets_bruts = requete.order_by(TrajetCamion.statut, TrajetCamion.date_creation).all()

    if utilisateur.profil == "agent_municipal":
        # Pas de lien direct commune <-> trajet en base : une tournée
        # est rattachée à la commune de l'agent si au moins un de ses
        # bacs s'y trouve. Filtrage en Python, cohérent avec le volume
        # limité attendu pour ce MVP.
        if utilisateur.commune_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ce compte n'est rattaché à aucune commune.",
            )
        bac_ids_commune = {
            str(row.id)
            for row in db.query(BacPublic.id)
            .filter(BacPublic.commune_id == utilisateur.commune_id)
            .all()
        }
        trajets_bruts = [
            t for t in trajets_bruts
            if any(p["bac_id"] in bac_ids_commune for p in t.liste_points_gps)
        ]

    total = len(trajets_bruts)
    trajets = trajets_bruts[offset:offset + limit]

    items = []
    for trajet in trajets:
        camion = db.query(Camion).filter(Camion.id == trajet.camion_id).first()
        entreprise = (
            db.query(EntrepriseCollecte).filter(EntrepriseCollecte.id == camion.entreprise_id).first()
            if camion else None
        )
        chauffeur = db.query(Utilisateur).filter(Utilisateur.id == trajet.chauffeur_id).first()

        nombre_bacs_total = len(trajet.liste_points_gps)
        nombre_bacs_collectes = sum(1 for p in trajet.liste_points_gps if p.get("collecte"))

        items.append(TrajetListeItem(
            id=trajet.id,
            date_trajet=trajet.date_trajet,
            statut=trajet.statut,
            camion_matricule=camion.matricule if camion else "N/A",
            entreprise_nom=entreprise.nom if entreprise else "N/A",
            chauffeur_nom=chauffeur.nom if chauffeur else "N/A",
            nombre_bacs_total=nombre_bacs_total,
            nombre_bacs_collectes=nombre_bacs_collectes,
        ))

    return TrajetListeReponse(items=items, total=total, limit=limit, offset=offset)