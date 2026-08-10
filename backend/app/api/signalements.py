"""
Endpoints API pour les signalements citoyens.

POST /signalements : point d'entrée principal de l'app mobile
côté citoyen. Reçoit la photo + les coordonnées, exécute la
vérification anti-fraude, puis enregistre le signalement.

GET /signalements : liste paginée pour les tableaux de bord
(agent municipal, entreprise de collecte, admin, ministère).
Lecture seule, inaccessible aux profils citoyen et chauffeur.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from geoalchemy2.functions import ST_Covers, ST_GeogFromText
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_utilisateur_courant, exiger_profil
from app.config import settings
from app.database import get_db
from app.models.bac_categorie import CategorieSignalement
from app.models.organisation import Commune
from app.models.photo import Photo, StatutVerificationPhoto
from app.models.signalement import Signalement, StatutSignalement, ModeSoumission
from app.models.utilisateur import Utilisateur, ProfilUtilisateur
from app.schemas.signalement import (
    SignalementReponse,
    SignalementListeReponse,
    SignalementListeItem,
    CategorieInfo,
    CommuneInfo,
)
from app.services.photo_verification import verifier_photo, point_vers_geography

router = APIRouter(prefix="/signalements", tags=["Signalements"])

# Profils autorisés à consulter la liste des signalements (dashboards).
# Le citoyen ne voit pas les signalements des autres (confidentialité).
# Le chauffeur a son propre périmètre via /trajets, pas besoin d'accès ici.
_PROFILS_DASHBOARD = (
    ProfilUtilisateur.agent_municipal,
    ProfilUtilisateur.entreprise,
    ProfilUtilisateur.admin,
    ProfilUtilisateur.ministere,
)


def _resoudre_categorie(code_categorie: str, db: Session) -> CategorieSignalement:
    """Retrouve la catégorie correspondant au code envoyé par l'app (ex: 'depot_sauvage')."""
    categorie = db.query(CategorieSignalement).filter(
        CategorieSignalement.code == code_categorie
    ).first()
    if categorie is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Catégorie inconnue : « {code_categorie} ».",
        )
    return categorie


def _resoudre_commune(latitude: float, longitude: float, db: Session) -> Commune:
    """
    Retrouve la commune dont la zone géographique contient le point donné,
    via une requête spatiale PostGIS. Évite de demander à l'app Flutter
    de connaître ou choisir la commune manuellement.
    """
    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    commune = db.query(Commune).filter(
        ST_Covers(Commune.zone_geo, ST_GeogFromText(point_wkt))
    ).first()

    if commune is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cette position ne correspond à aucune commune connue du District Autonome d'Abidjan.",
        )
    return commune


@router.get("", response_model=SignalementListeReponse)
def lister_signalements(
    commune_id: uuid.UUID | None = Query(None, description="Filtrer par commune"),
    statut: StatutSignalement | None = Query(None, description="Filtrer par statut"),
    categorie_id: uuid.UUID | None = Query(None, description="Filtrer par catégorie"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    utilisateur: Utilisateur = Depends(exiger_profil(*_PROFILS_DASHBOARD)),
    db: Session = Depends(get_db),
):
    """
    Liste les signalements citoyens pour les tableaux de bord municipaux,
    entreprises et ministériels. Lecture seule, triée du plus récent au
    plus ancien.

    NOTE MVP : accessible à tous les profils du dashboard sans filtrage
    automatique par commune/entreprise -- le role-scoping strict (agent
    municipal limité à sa commune, entreprise à sa flotte) est prévu "à
    terme" mais pas requis pour le prototype démontrable. Les filtres
    query params ci-dessous permettent déjà de circonscrire les résultats
    manuellement en attendant cette évolution.
    """
    requete = db.query(Signalement).options(
        joinedload(Signalement.categorie),
        joinedload(Signalement.commune),
        joinedload(Signalement.utilisateur),
    )

    if commune_id is not None:
        requete = requete.filter(Signalement.commune_id == commune_id)
    if statut is not None:
        requete = requete.filter(Signalement.statut == statut)
    if categorie_id is not None:
        requete = requete.filter(Signalement.categorie_id == categorie_id)

    total = requete.count()

    signalements = (
        requete
        .order_by(Signalement.date_creation.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items = []
    for s in signalements:
        point = to_shape(s.coordonnees_gps)
        items.append(SignalementListeItem(
            id=s.id,
            statut=s.statut.value,
            mode_soumission=s.mode_soumission.value,
            date_creation=s.date_creation,
            date_resolution=s.date_resolution,
            categorie=CategorieInfo(libelle=s.categorie.libelle, code=s.categorie.code),
            commune=CommuneInfo(nom=s.commune.nom),
            citoyen_nom=s.utilisateur.nom,
            latitude=point.y,
            longitude=point.x,
        ))

    return SignalementListeReponse(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=SignalementReponse, status_code=status.HTTP_201_CREATED)
async def creer_signalement(
    categorie: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    bac_id: str | None = Form(None),
    mode_soumission: ModeSoumission = Form(ModeSoumission.en_ligne),
    photo: UploadFile = File(...),
    utilisateur: Utilisateur = Depends(get_utilisateur_courant),
    db: Session = Depends(get_db),
):
    """
    Crée un nouveau signalement pour l'utilisateur actuellement authentifié.
    La photo est obligatoire et passe systématiquement par la vérification
    anti-fraude avant que le signalement soit accepté. La commune est
    déduite automatiquement des coordonnées GPS.
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

    categorie_resolue = _resoudre_categorie(categorie, db)
    commune_resolue = _resoudre_commune(latitude, longitude, db)

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
        utilisateur_id=utilisateur.id,
        categorie_id=categorie_resolue.id,
        commune_id=commune_resolue.id,
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