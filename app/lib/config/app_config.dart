/// Configuration centrale de l'application.
///
/// IMPORTANT : adapte `apiBaseUrl` selon l'environnement de test :
/// - Flutter Web (Chrome) sur le même PC que l'API -> http://localhost:8000
/// - Émulateur Android -> http://10.0.2.2:8000
/// - Téléphone Android réel sur le même Wi-Fi -> http://<IP_LOCALE_DU_PC>:8000
class AppConfig {
  static const String apiBaseUrl = 'http://10.0.2.2:8000';

  static const String signalementsEndpoint = '/signalements';

  static const String trajetsEndpoint = '/trajets/aujourdhui';

  static String collecterBacEndpoint(String trajetId, String bacId) =>
    '/trajets/$trajetId/bacs/$bacId/collecter';

  /// Délai max avant de considérer qu'il n'y a pas de connexion utile.
  static const Duration apiTimeout = Duration(seconds: 10);

  /// Token public Mapbox, injecté au lancement via --dart-define
  /// (voir .vscode/launch.json). Jamais codé en dur ici.
  static const String mapboxAccessToken =
      String.fromEnvironment('MAPBOX_ACCESS_TOKEN');

  /// API Directions Mapbox, utilisée pour tracer l'itinéraire du chauffeur
  /// vers le prochain bac non collecté (distincte de l'API Matrix utilisée
  /// côté backend pour l'optimisation d'ordre des bacs).
  static const String mapboxDirectionsBaseUrl =
      'https://api.mapbox.com/directions/v5/mapbox/driving';
}