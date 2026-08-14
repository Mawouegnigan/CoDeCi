"""
Service de vérification anti-fraude des photos de signalement.

Deux contrôles au MVP (peu coûteux, exécutés côté serveur) :
1. Cohérence EXIF : la photo doit avoir été prise récemment et,
   si elle contient un GPS EXIF, il doit être cohérent avec la
   position déclarée par le citoyen (tolérance définie en config).
2. Hash perceptuel : détecte la réutilisation d'une photo déjà
   soumise (même approximativement recadrée/compressée).

L'analyse par IA du contenu (vérifier que la photo montre bien
des déchets) est prévue en phase 2 - non incluse ici.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO

import imagehash
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

import base64

import anthropic

from app.config import settings
from app.models.photo import Photo, StatutVerificationPhoto

# Une photo plus vieille que ça au moment de l'envoi est jugée suspecte
AGE_MAX_PHOTO = timedelta(hours=24)

_PROMPT_VERIFICATION_IA = (
    "Tu vérifies des photos soumises par des citoyens pour signaler des "
    "déchets à collecter en Côte d'Ivoire (dépôts sauvages, poubelles "
    "débordantes, ordures accumulées). Réponds uniquement par 'OUI' si "
    "la photo montre clairement des déchets ou des ordures, ou par 'NON' "
    "si elle ne montre pas de déchets (photo hors-sujet, floue au point "
    "d'être inexploitable, ou trompeuse). Un seul mot, rien d'autre."
)


def _verifier_contenu_ia(contenu_fichier: bytes) -> tuple[bool, str | None]:
    """
    Interroge un modèle de vision pour confirmer que la photo montre bien
    des déchets. Renvoie (contenu_valide, motif_si_invalide).

    Défaillant en douceur : si l'appel échoue (réseau, quota, clé absente)
    ou si la vérification est désactivée en config, on considère le
    contenu comme valide plutôt que de bloquer un citoyen à cause d'un
    problème indépendant de sa soumission -- l'EXIF et le hash restent
    les contrôles obligatoires, l'IA est une couche additionnelle.
    """
    if not settings.verification_ia_active:
        return True, None

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        image_b64 = base64.standard_b64encode(contenu_fichier).decode("utf-8")

        reponse = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": _PROMPT_VERIFICATION_IA},
                ],
            }],
        )

        texte = reponse.content[0].text.strip().upper()
        if texte.startswith("OUI"):
            return True, None
        return False, "La photo ne semble pas montrer de déchets — à vérifier manuellement."

    except Exception:
        # On ne bloque jamais un signalement à cause d'un souci technique
        # côté IA (clé absente, quota, réseau). Les autres contrôles
        # (EXIF, hash) restent les garde-fous obligatoires.
        return True, None


@dataclass
class ResultatVerification:
    statut: StatutVerificationPhoto
    motif_rejet: str | None
    hash_perceptuel: str
    exif_date: datetime | None
    exif_point: Point | None


def _extraire_exif(image: Image.Image) -> dict:
    """Extrait les métadonnées EXIF brutes d'une image PIL, y compris le GPS."""
    exif_brut = image._getexif() or {}
    exif = {}
    for tag_id, valeur in exif_brut.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag == "GPSInfo":
            gps_data = {}
            for gps_tag_id, gps_valeur in valeur.items():
                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                gps_data[gps_tag] = gps_valeur
            exif["GPSInfo"] = gps_data
        else:
            exif[tag] = valeur
    return exif


def _dms_vers_degres_decimaux(dms, ref) -> float:
    degres, minutes, secondes = dms
    valeur = float(degres) + float(minutes) / 60 + float(secondes) / 3600
    if ref in ("S", "W"):
        valeur = -valeur
    return valeur


def _extraire_gps_exif(exif: dict) -> Point | None:
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        return None
    try:
        lat = _dms_vers_degres_decimaux(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
        lon = _dms_vers_degres_decimaux(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
        return Point(lon, lat)
    except (KeyError, ValueError, ZeroDivisionError):
        return None


def _extraire_date_exif(exif: dict) -> datetime | None:
    date_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _distance_metres(point_a: Point, point_b: Point) -> float:
    """
    Approximation rapide en mètres (formule équirectangulaire) --
    suffisante pour un simple contrôle de tolérance, pas pour du routage.
    """
    import math

    rayon_terre = 6371000
    lat1, lon1 = math.radians(point_a.y), math.radians(point_a.x)
    lat2, lon2 = math.radians(point_b.y), math.radians(point_b.x)
    dx = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
    dy = lat2 - lat1
    return math.sqrt(dx * dx + dy * dy) * rayon_terre


def verifier_photo(
    contenu_fichier: bytes,
    position_declaree: Point,
    db: Session,
) -> ResultatVerification:
    """
    Analyse une photo nouvellement soumise et détermine si elle est
    valide, suspecte (à revoir par un admin) ou rejetée d'office.
    """
    image = Image.open(BytesIO(contenu_fichier))

    hash_perceptuel = str(imagehash.phash(image))
    exif = _extraire_exif(image)
    exif_date = _extraire_date_exif(exif)
    exif_point = _extraire_gps_exif(exif)

    # 1. Détection de réutilisation : même hash déjà présent en base
    doublon = db.query(Photo).filter(Photo.hash_perceptuel == hash_perceptuel).first()
    if doublon is not None:
        return ResultatVerification(
            statut=StatutVerificationPhoto.rejetee,
            motif_rejet="Photo déjà soumise précédemment (hash identique détecté).",
            hash_perceptuel=hash_perceptuel,
            exif_date=exif_date,
            exif_point=exif_point,
        )

    # 2. Fraîcheur de la photo
    if exif_date is not None:
        maintenant = datetime.now(timezone.utc)
        if maintenant - exif_date > AGE_MAX_PHOTO:
            return ResultatVerification(
                statut=StatutVerificationPhoto.suspecte,
                motif_rejet="Photo prise il y a plus de 24h — à vérifier manuellement.",
                hash_perceptuel=hash_perceptuel,
                exif_date=exif_date,
                exif_point=exif_point,
            )

    # 3. Cohérence GPS EXIF vs position déclarée
    if exif_point is not None:
        distance = _distance_metres(exif_point, position_declaree)
        if distance > settings.gps_tolerance_meters:
            return ResultatVerification(
                statut=StatutVerificationPhoto.suspecte,
                motif_rejet=(
                    f"Position GPS de la photo ({distance:.0f}m) incohérente "
                    f"avec la position déclarée — à vérifier manuellement."
                ),
                hash_perceptuel=hash_perceptuel,
                exif_date=exif_date,
                exif_point=exif_point,
            )

    # 4. Vérification IA du contenu (Claude vision) -- dernière étape,
    # seulement si tous les contrôles précédents sont passés.
    contenu_valide, motif_ia = _verifier_contenu_ia(contenu_fichier)
    if not contenu_valide:
        return ResultatVerification(
            statut=StatutVerificationPhoto.suspecte,
            motif_rejet=motif_ia,
            hash_perceptuel=hash_perceptuel,
            exif_date=exif_date,
            exif_point=exif_point,
        )

    return ResultatVerification(
        statut=StatutVerificationPhoto.valide,
        motif_rejet=None,
        hash_perceptuel=hash_perceptuel,
        exif_date=exif_date,
        exif_point=exif_point,
    )


def point_vers_geography(point: Point):
    """Convertit un point Shapely en objet compatible GeoAlchemy2/PostGIS."""
    return from_shape(point, srid=4326)
