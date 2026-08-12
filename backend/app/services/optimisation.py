"""
Service d'optimisation de tournées : construit une matrice de temps de
trajet via l'API Mapbox Matrix, puis résout l'ordre optimal de passage
avec OR-Tools (TSP à 1 véhicule).

Simplification MVP assumée : le premier point de la liste sert de "dépôt"
de départ pour le calcul (pas de garage/entrepôt distinct en base pour
l'instant). À revoir si un jour les camions ont une position de départ
propre, indépendante du premier bac.
"""
import requests
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from app.config import settings


class ErreurOptimisation(Exception):
    """Erreur levée quand la matrice de distances ou la résolution échoue."""
    pass


def obtenir_matrice_durees(points: list[dict]) -> list[list[float]]:
    """
    Interroge l'API Mapbox Matrix pour obtenir les temps de trajet routiers
    (en secondes) entre chaque paire de points.

    points : liste de dicts contenant au moins 'latitude' et 'longitude'.
    Limite Mapbox : 25 points maximum par appel (largement suffisant pour
    une tournée de bacs en MVP).
    """
    if len(points) > 25:
        raise ErreurOptimisation(
            "L'API Mapbox Matrix limite à 25 points par tournée "
            f"(cette tournée en a {len(points)})."
        )

    coordonnees = ";".join(
        f"{p['longitude']},{p['latitude']}" for p in points
    )
    url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coordonnees}"

    reponse = requests.get(
        url,
        params={
            "annotations": "duration",
            "access_token": settings.mapbox_token,
        },
        timeout=10,
    )

    if reponse.status_code != 200:
        raise ErreurOptimisation(
            f"Erreur Mapbox Matrix API ({reponse.status_code}) : {reponse.text}"
        )

    data = reponse.json()
    durees = data.get("durations")
    if durees is None:
        raise ErreurOptimisation("Réponse Mapbox invalide : pas de champ 'durations'.")

    return durees


def resoudre_ordre_optimal(matrice_durees: list[list[float]]) -> list[int]:
    """
    Résout le TSP (1 véhicule, part de l'index 0) à partir d'une matrice
    de durées. Renvoie la liste des indices dans l'ordre de passage optimal.
    """
    nombre_points = len(matrice_durees)
    gestionnaire = pywrapcp.RoutingIndexManager(nombre_points, 1, 0)
    routage = pywrapcp.RoutingModel(gestionnaire)

    def callback_duree(index_depart, index_arrivee):
        noeud_depart = gestionnaire.IndexToNode(index_depart)
        noeud_arrivee = gestionnaire.IndexToNode(index_arrivee)
        return int(matrice_durees[noeud_depart][noeud_arrivee])

    indice_callback = routage.RegisterTransitCallback(callback_duree)
    routage.SetArcCostEvaluatorOfAllVehicles(indice_callback)

    parametres = pywrapcp.DefaultRoutingSearchParameters()
    parametres.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routage.SolveWithParameters(parametres)
    if solution is None:
        raise ErreurOptimisation("OR-Tools n'a pas trouvé de solution pour cette tournée.")

    ordre = []
    index = routage.Start(0)
    while not routage.IsEnd(index):
        ordre.append(gestionnaire.IndexToNode(index))
        index = solution.Value(routage.NextVar(index))

    return ordre


def optimiser_tournee(points: list[dict]) -> list[dict]:
    """
    Point d'entrée du service : prend la liste de points d'un trajet
    (telle que stockée dans liste_points_gps) et renvoie la même liste
    réordonnée selon le trajet optimal, avec le champ 'ordre' mis à jour.
    """
    matrice = obtenir_matrice_durees(points)
    ordre_optimal = resoudre_ordre_optimal(matrice)

    points_reordonnes = [points[i] for i in ordre_optimal]
    for nouvel_ordre, point in enumerate(points_reordonnes):
        point["ordre"] = nouvel_ordre

    return points_reordonnes