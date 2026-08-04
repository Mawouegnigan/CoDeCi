"""
Modèle Photo : centralise tout ce qui concerne la vérification
anti-fraude (hash perceptuel, EXIF) et le cycle de vie de rétention.
"""

import uuid
import enum
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class StatutVerificationPhoto(str, enum.Enum):
    en_attente = "en_attente"
    valide = "valide"
    suspecte = "suspecte"
    rejetee = "rejetee"


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nullable : le fichier est supprimé après la période de rétention,
    # mais la ligne (et le hash) reste en base pour l'anti-fraude et l'audit.
    url_fichier = Column(Text, nullable=True)

    hash_perceptuel = Column(String(64), nullable=False, index=True)
    exif_gps = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    exif_date = Column(DateTime(timezone=True), nullable=True)

    statut_verification = Column(
        Enum(StatutVerificationPhoto), nullable=False, default=StatutVerificationPhoto.en_attente
    )
    motif_rejet = Column(Text, nullable=True)

    date_upload = Column(DateTime(timezone=True), default=datetime.utcnow)
    date_suppression_fichier = Column(DateTime(timezone=True), nullable=True)
