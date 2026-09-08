"""
Service de gestion du système de points citoyens : crédit (signalements
résolus) et conversion en mobile money (MTN MoMo Disbursement).

Toute modification du solde d'un utilisateur DOIT passer par ce
service, jamais par une écriture directe sur `Utilisateur.solde_points`.
C'est ce qui garantit que le solde affiché correspond toujours à la
somme des mouvements du registre `transactions_points`.
"""

from sqlalchemy.orm import Session

from app.models.operations import TransactionPoints, TypeTransactionPoints, StatutTransactionPoints
from app.models.signalement import Signalement
from app.models.utilisateur import Utilisateur
from app.services.momo_service import obtenir_provider_momo

POINTS_PAR_SIGNALEMENT_RESOLU = 10
TAUX_FCFA_PAR_POINT = 5
SEUIL_MINIMUM_CONVERSION = 50


class SoldeInsuffisantError(Exception):
    """Levée quand un citoyen tente une conversion sous le seuil minimum."""
    pass


def crediter_points_signalement(signalement: Signalement, db: Session) -> TransactionPoints | None:
    """
    Crédite les points d'un signalement résolu à son auteur.

    Idempotent : si ce signalement a déjà été crédité (contrainte
    unique en base sur signalement_id), renvoie None sans rien modifier
    plutôt que de lever une exception -- un appelant comme collecter_bac
    ne doit jamais planter sur un doublon inoffensif.

    N'effectue pas de commit : la transaction est laissée à la charge
    de l'appelant, pour que crédit de points et mise à jour du statut
    du signalement restent atomiques dans une seule transaction DB.
    """
    deja_credite = db.query(TransactionPoints).filter(
        TransactionPoints.signalement_id == signalement.id
    ).first()
    if deja_credite is not None:
        return None

    utilisateur = (
        db.query(Utilisateur)
        .filter(Utilisateur.id == signalement.utilisateur_id)
        .with_for_update()
        .first()
    )
    if utilisateur is None:
        return None

    transaction = TransactionPoints(
        utilisateur_id=utilisateur.id,
        type=TypeTransactionPoints.gain_signalement,
        montant_points=POINTS_PAR_SIGNALEMENT_RESOLU,
        signalement_id=signalement.id,
        statut=StatutTransactionPoints.reussi,
    )
    db.add(transaction)
    utilisateur.solde_points += POINTS_PAR_SIGNALEMENT_RESOLU
    db.flush()

    return transaction


def demander_conversion_momo(utilisateur_id, db: Session) -> TransactionPoints:
    """
    Convertit la totalité des points disponibles d'un citoyen en FCFA
    via MTN MoMo Disbursement (ou son simulateur, MockMomoProvider).

    Débite immédiatement les points (statut initial en_attente) avant
    même de connaître le résultat du paiement : ceci empêche un
    citoyen de soumettre plusieurs demandes de conversion en rafale
    avant qu'aucune ne soit confirmée (double-dépense). Le verrou
    with_for_update sur la ligne utilisateur empêche aussi deux
    requêtes concurrentes de lire le même solde avant débit.

    Si le paiement échoue, les points sont recrédités via une NOUVELLE
    ligne (type=annulation_conversion) plutôt qu'en modifiant la ligne
    de débit d'origine -- celle-ci reste un enregistrement immuable de
    la tentative échouée, consultable pour audit.

    Lève SoldeInsuffisantError si le solde est sous le seuil minimum.
    N'effectue pas de commit : laissé à la charge de l'appelant.
    """
    utilisateur = (
        db.query(Utilisateur)
        .filter(Utilisateur.id == utilisateur_id)
        .with_for_update()
        .first()
    )
    if utilisateur is None:
        raise ValueError("Utilisateur introuvable.")

    if utilisateur.solde_points < SEUIL_MINIMUM_CONVERSION:
        raise SoldeInsuffisantError(
            f"Solde insuffisant : {utilisateur.solde_points} points, "
            f"minimum requis {SEUIL_MINIMUM_CONVERSION}."
        )

    points_a_convertir = utilisateur.solde_points
    montant_fcfa = points_a_convertir * TAUX_FCFA_PAR_POINT

    utilisateur.solde_points = 0

    transaction_debit = TransactionPoints(
        utilisateur_id=utilisateur.id,
        type=TypeTransactionPoints.conversion_mobile_money,
        montant_points=points_a_convertir,
        montant_fcfa=montant_fcfa,
        numero_telephone=utilisateur.telephone,
        statut=StatutTransactionPoints.en_attente,
    )
    db.add(transaction_debit)
    db.flush()

    provider = obtenir_provider_momo()
    resultat = provider.disburser(utilisateur.telephone, montant_fcfa)

    if resultat.reussi:
        transaction_debit.statut = StatutTransactionPoints.reussi
        transaction_debit.reference_externe = resultat.reference_externe
    else:
        transaction_debit.statut = StatutTransactionPoints.echoue
        transaction_debit.reference_externe = resultat.reference_externe

        utilisateur.solde_points += points_a_convertir
        transaction_compensation = TransactionPoints(
            utilisateur_id=utilisateur.id,
            type=TypeTransactionPoints.annulation_conversion,
            montant_points=points_a_convertir,
            statut=StatutTransactionPoints.reussi,
            reference_externe=resultat.reference_externe,
        )
        db.add(transaction_compensation)

    db.flush()
    return transaction_debit