/// Configuration centrale de l'application.
///
/// IMPORTANT : adapte `apiBaseUrl` selon l'environnement de test :
/// - Flutter Web (Chrome) sur le même PC que l'API -> http://localhost:8000
/// - Émulateur Android -> http://10.0.2.2:8000
/// - Téléphone Android réel sur le même Wi-Fi -> http://<IP_LOCALE_DU_PC>:8000
class AppConfig {
  static const String apiBaseUrl = 'http://localhost:8000';

  static const String signalementsEndpoint = '/signalements';

  /// Délai max avant de considérer qu'il n'y a pas de connexion utile.
  static const Duration apiTimeout = Duration(seconds: 10);
}