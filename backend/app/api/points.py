"""
Endpoints citoyen pour le système de points : consultation du solde,
historique des transactions, et conversion en mobile money via MTN
MoMo Disbursement (simulé tant que le compte développeur MTN n'est
pas créé -- voir app/services/momo_service.py).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import exiger_profil
from app.database import get_db
from app.models.operations import TransactionPoints
from app.models.utilisateur import Utilisateur, ProfilUtilisateur
from app.schemas.points import (
    SoldeCitoyenReponse,
    ConversionReponse,
    TransactionPointsItem,
    TransactionPointsListeReponse,
)
from app.services.points_service import demander_conversion_momo, SoldeInsuffisantError

router = APIRouter(prefix="/citoyen/points", tags=["Points citoyen"])


@router.get("/solde", response_model=SoldeCitoyenReponse)
def consulter_solde(
    utilisateur: Utilisateur = Depends(exiger_profil(ProfilUtilisateur.citoyen)),
):
    """Renvoie le solde de points actuel du citoyen connecté."""
    return SoldeCitoyenReponse(solde_points=utilisateur.solde_points)


@router.get("/transactions", response_model=TransactionPointsListeReponse)
def lister_transactions(
    utilisateur: Utilisateur = Depends(exiger_profil(ProfilUtilisateur.citoyen)),
    db: Session = Depends(get_db),
):
    """Historique complet des mouvements de points du citoyen connecté."""
    transactions = (
        db.query(TransactionPoints)
        .filter(TransactionPoints.utilisateur_id == utilisateur.id)
        .order_by(TransactionPoints.date_creation.desc())
        .all()
    )
    items = [
        TransactionPointsItem(
            id=t.id,
            type=t.type.value,
            statut=t.statut.value,
            montant_points=t.montant_points,
            montant_fcfa=t.montant_fcfa,
            reference_externe=t.reference_externe,
            date_creation=t.date_creation,
        )
        for t in transactions
    ]
    return TransactionPointsListeReponse(items=items, total=len(items))


@router.post("/convertir", response_model=ConversionReponse)
def convertir_points(
    utilisateur: Utilisateur = Depends(exiger_profil(ProfilUtilisateur.citoyen)),
    db: Session = Depends(get_db),
):
    """
    Convertit la totalité du solde de points du citoyen connecté en
    FCFA, versé via MTN MoMo Disbursement sur son propre numéro de
    téléphone (celui du compte CoDeCI).
    """
    try:
        transaction = demander_conversion_momo(utilisateur.id, db)
    except SoldeInsuffisantError as erreur:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erreur))

    db.commit()
    db.refresh(transaction)

    if transaction.statut.value == "reussi":
        message = f"{transaction.montant_fcfa} FCFA envoyés avec succès sur {transaction.numero_telephone}."
    else:
        message = "Le paiement a échoué, vos points ont été recrédités automatiquement."

    return ConversionReponse(
        id=transaction.id,
        statut=transaction.statut.value,
        montant_points=transaction.montant_points,
        montant_fcfa=transaction.montant_fcfa,
        reference_externe=transaction.reference_externe,
        message=message,
    )