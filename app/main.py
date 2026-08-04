"""
Point d'entrée de l'API CoDeCI.
Lancer avec : uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api import signalements

app = FastAPI(
    title="CoDeCI API",
    description="API de la plateforme de collecte de déchets - Côte d'Ivoire",
    version="0.1.0",
)

app.include_router(signalements.router)


@app.get("/", tags=["Santé"])
def verifier_etat():
    """Endpoint simple pour vérifier que l'API tourne correctement."""
    return {"statut": "ok", "service": "CoDeCI API"}
