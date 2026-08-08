"""
Configuration centralisée de l'application CoDeCI.
Toutes les valeurs sensibles ou variables selon l'environnement
(dev / production) passent par ici, jamais codées en dur ailleurs.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://codeci_user:motdepasse@localhost:5432/codeci_db"
    photo_storage_path: str = "./storage/photos"
    photo_retention_days: int = 90
    gps_tolerance_meters: int = 150

    # Authentification JWT
    # IMPORTANT : jwt_secret_key DOIT être surchargée via .env en production
    # (jamais la valeur par défaut ci-dessous, elle n'est là que pour le dev local).
    jwt_secret_key: str = "change-moi-dans-le-.env-avant-la-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 jours

    class Config:
        env_file = ".env"


settings = Settings()