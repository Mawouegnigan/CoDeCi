"""
Abstraction du fournisseur de paiement mobile money (MTN MoMo
Disbursement). Deux implémentations : MockMomoProvider (active tant
que le compte MTN MoMo Developer n'est pas créé, simule le paiement
sans appel réseau) et MTNMomoDisbursementProvider (à compléter une
fois les clés sandbox/production obtenues).

Bascule via la variable d'environnement MOMO_MODE : "simulation"
(défaut) ou "production". Même principe que verification_ia_active
pour la vérification photo -- un flag, pas une réécriture de code.
"""

import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ResultatDisbursement:
    reussi: bool
    reference_externe: str
    message: str


class MomoProvider(ABC):
    @abstractmethod
    def disburser(self, numero_telephone: str, montant_fcfa: int) -> ResultatDisbursement:
        ...


class MockMomoProvider(MomoProvider):
    """
    Simule un paiement MTN MoMo Disbursement, sans appel réseau réel.
    Permet de développer et démontrer le flux de conversion complet
    avant l'obtention des clés API.

    Un numéro de téléphone se terminant par '000' déclenche un échec
    simulé -- utile pour tester le recrédit de points sans dépendre
    du hasard.
    """

    def disburser(self, numero_telephone: str, montant_fcfa: int) -> ResultatDisbursement:
        reference_simulee = f"MOCK-{uuid.uuid4().hex[:12]}"

        if numero_telephone.endswith("000"):
            return ResultatDisbursement(
                reussi=False,
                reference_externe=reference_simulee,
                message="Échec simulé (numéro de test se terminant par 000).",
            )

        return ResultatDisbursement(
            reussi=True,
            reference_externe=reference_simulee,
            message="Paiement simulé avec succès (mode simulation MTN MoMo).",
        )


class MTNMomoDisbursementProvider(MomoProvider):
    """
    Intégration réelle avec l'API MTN MoMo Disbursement. À implémenter
    une fois le compte développeur MTN MoMo créé (subscription key,
    API user/key, target environment sandbox puis production).
    Ne pas activer avant d'avoir ces identifiants.
    """

    def disburser(self, numero_telephone: str, montant_fcfa: int) -> ResultatDisbursement:
        raise NotImplementedError(
            "Intégration MTN MoMo réelle non encore implémentée. "
            "Laisser MOMO_MODE=simulation dans .env en attendant."
        )


def obtenir_provider_momo() -> MomoProvider:
    """Sélectionne le provider actif selon la variable d'environnement MOMO_MODE."""
    if os.getenv("MOMO_MODE", "simulation") == "production":
        return MTNMomoDisbursementProvider()
    return MockMomoProvider()