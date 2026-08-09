"""
Point d'entrée de l'API CoDeCI.
Lancer avec : uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import signalements, auth, trajets

app = FastAPI(
    title="CoDeCI API",
    description="API de la plateforme de collecte de déchets - Côte d'Ivoire",
    version="0.1.0",
)

# Autorise l'app Flutter (web pendant le développement, puis mobile) à
# appeler l'API. En développement on ouvre largement ; à restreindre à
# de vrais domaines une fois en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(signalements.router)
app.include_router(trajets.router)


@app.get("/", tags=["Santé"])
def verifier_etat():
    """Endpoint simple pour vérifier que l'API tourne correctement."""
    return {"statut": "ok", "service": "CoDeCI API"}