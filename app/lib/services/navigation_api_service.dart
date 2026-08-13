import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';

/// Erreur levée quand le calcul d'itinéraire échoue (réseau, Mapbox, etc.).
class ErreurNavigation implements Exception {
  final String message;
  ErreurNavigation(this.message);

  @override
  String toString() => message;
}

/// Résultat d'un calcul d'itinéraire : tracé géographique + estimations.
class ItineraireResultat {
  final List<List<double>> geometrie; // paires [longitude, latitude]
  final double distanceMetres;
  final double dureeSecondes;

  ItineraireResultat({
    required this.geometrie,
    required this.distanceMetres,
    required this.dureeSecondes,
  });
}

/// Couche responsable UNIQUEMENT de parler à l'API Directions de Mapbox,
/// pour tracer l'itinéraire du chauffeur vers le prochain bac.
class NavigationApiService {
  Future<ItineraireResultat> obtenirItineraire({
    required double departLatitude,
    required double departLongitude,
    required double arriveeLatitude,
    required double arriveeLongitude,
  }) async {
    final coordonnees =
        '$departLongitude,$departLatitude;$arriveeLongitude,$arriveeLatitude';

    final uri = Uri.parse('${AppConfig.mapboxDirectionsBaseUrl}/$coordonnees')
        .replace(queryParameters: {
      'geometries': 'geojson',
      'overview': 'full',
      'access_token': AppConfig.mapboxAccessToken,
    });

    try {
      final response = await http.get(uri).timeout(AppConfig.apiTimeout);

      if (response.statusCode != 200) {
        String detail = '';
        try {
          final corps = jsonDecode(response.body) as Map<String, dynamic>;
          detail = corps['message']?.toString() ?? '';
        } catch (_) {
          // corps non exploitable, on garde detail vide
        }
        throw ErreurNavigation(
          'Erreur Mapbox Directions (${response.statusCode})'
          '${detail.isNotEmpty ? ' : $detail' : ''}.',
        );
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final routes = data['routes'] as List?;
      if (routes == null || routes.isEmpty) {
        throw ErreurNavigation("Aucun itinéraire trouvé vers ce bac.");
      }

      final route = routes.first as Map<String, dynamic>;
      final geometrie = route['geometry'] as Map<String, dynamic>;
      final coordonneesTracees = (geometrie['coordinates'] as List)
          .map((point) => (point as List)
              .map((valeur) => (valeur as num).toDouble())
              .toList())
          .toList();

      return ItineraireResultat(
        geometrie: coordonneesTracees,
        distanceMetres: (route['distance'] as num).toDouble(),
        dureeSecondes: (route['duration'] as num).toDouble(),
      );
    } on ErreurNavigation {
      rethrow;
    } catch (e) {
      throw ErreurNavigation("Impossible de calculer l'itinéraire : $e");
    }
  }
}