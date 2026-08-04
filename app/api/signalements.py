"""
Endpoints API pour les signalements citoyens.

POST /signalements : point d'entrée principal de l'app mobile
côté citoyen. Reçoit la photo + les coordonnées, exécute la
vérification anti-fraude, puis enregistre le signalement.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.photo import Photo, StatutVerificationPhoto
from app.models.signalement import Signalement, StatutSignalement, ModeSoumission
from app.schemas.signalement import SignalementReponse
from app.services.photo_verification import verifier_photo, point_vers_geography

router = APIRouter(prefix="/signalements", tags=["Signalements"])


@router.post("", response_model=SignalementReponse, status_code=status.HTTP_201_CREATED)
async def creer_signalement(
    utilisateur_id: uuid.UUID = Form(...),
    categorie_id: uuid.UUID = Form(...),
    commune_id: uuid.UUID = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    bac_id: str | None = Form(None),
    mode_soumission: ModeSoumission = Form(ModeSoumission.en_ligne),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Crée un nouveau signalement. La photo est obligatoire et passe
    systématiquement par la vérification anti-fraude avant que le
    signalement soit accepté.
    """
    bac_id_uuid = None
    if bac_id:
        try:
            bac_id_uuid = uuid.UUID(bac_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"bac_id invalide : « {bac_id} » n'est pas un UUID valide. Laissez le champ vide s'il n'y a pas de bac associé.",
            )
    contenu_photo = await photo.read()
    position_declaree = Point(longitude, latitude)

    resultat = verifier_photo(contenu_photo, position_declaree, db)

    if resultat.statut == StatutVerificationPhoto.rejetee:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=resultat.motif_rejet,
        )

    # Sauvegarde du fichier sur disque (à remplacer par un stockage
    # objet type S3/Spaces dès le passage en production)
    dossier_stockage = Path(settings.photo_storage_path)
    dossier_stockage.mkdir(parents=True, exist_ok=True)
    nom_fichier = f"{uuid.uuid4()}{Path(photo.filename or 'photo.jpg').suffix}"
    chemin_fichier = dossier_stockage / nom_fichier
    with open(chemin_fichier, "wb") as f:
        f.write(contenu_photo)

    nouvelle_photo = Photo(
        url_fichier=str(chemin_fichier),
        hash_perceptuel=resultat.hash_perceptuel,
        exif_gps=point_vers_geography(resultat.exif_point) if resultat.exif_point else None,
        exif_date=resultat.exif_date,
        statut_verification=resultat.statut,
        motif_rejet=resultat.motif_rejet,
    )
    db.add(nouvelle_photo)
    db.flush()  # récupère l'id généré sans committer tout de suite

    # Une photo "suspecte" crée quand même le signalement, mais il
    # part directement en file d'attente pour revue manuelle admin
    # plutôt qu'un statut normal -- pas de points crédités automatiquement.
    nouveau_signalement = Signalement(
        utilisateur_id=utilisateur_id,
        categorie_id=categorie_id,
        commune_id=commune_id,
        bac_id=bac_id_uuid,
        photo_id=nouvelle_photo.id,
        coordonnees_gps=point_vers_geography(position_declaree),
        statut=StatutSignalement.en_attente,
        mode_soumission=mode_soumission,
    )
    db.add(nouveau_signalement)
    db.commit()
    db.refresh(nouveau_signalement)

    return SignalementReponse(
        id=nouveau_signalement.id,
        statut=nouveau_signalement.statut.value,
        mode_soumission=nouveau_signalement.mode_soumission.value,
        categorie_id=nouveau_signalement.categorie_id,
        commune_id=nouveau_signalement.commune_id,
        date_creation=nouveau_signalement.date_creation,
        photo_statut_verification=resultat.statut.value,
        motif_rejet=resultat.motif_rejet,
    )
