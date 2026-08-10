import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../models/signalement.dart';
import '../services/api_service.dart';
import '../services/queue_service.dart';

/// Résultat renvoyé à l'UI après une tentative de soumission,
/// pour lui permettre d'afficher le bon message sans connaître
/// les détails de l'implémentation réseau.
enum ResultatSoumission { envoye, misEnAttente, rejete, sessionExpiree }

class SoumissionResult {
  final ResultatSoumission resultat;
  final String? messageErreur;
  SoumissionResult(this.resultat, {this.messageErreur});
}

/// Point d'entrée UNIQUE pour l'UI : elle ne sait jamais si on est
/// en ligne, hors-ligne, ou en train de resynchroniser. Elle appelle
/// juste submitSignalement() et affiche le résultat.
class SignalementRepository {
  final ApiService _apiService;
  final QueueService _queueService;

  /// Fournit le token JWT courant au moment de l'envoi (pas au moment de
  /// la création du Repository), pour toujours utiliser un token à jour
  /// même si l'utilisateur se reconnecte entre-temps.
  final String? Function() _obtenirToken;

  final _syncController = StreamController<int>.broadcast();

  /// Émet le nombre de signalements encore en attente à chaque
  /// changement, pour que l'UI puisse afficher un badge par exemple.
  Stream<int> get enAttenteStream => _syncController.stream;

  SignalementRepository({
    required String? Function() obtenirToken,
    ApiService? apiService,
    QueueService? queueService,
  })  : _obtenirToken = obtenirToken,
        _apiService = apiService ?? ApiService(),
        _queueService = queueService ?? QueueService();

  Future<void> init() async {
    await _queueService.init();
    _notifierEnAttente();
  }

  void _notifierEnAttente() {
    _syncController.add(_queueService.nombreEnAttente);
  }

  Future<SoumissionResult> submitSignalement(Signalement signalement) async {
    try {
      await _apiService.envoyerSignalement(signalement, token: _obtenirToken());
      return SoumissionResult(ResultatSoumission.envoye);
    } on ApiAuthException catch (e) {
      // Token expiré/invalide : on NE met PAS en file (ça échouerait à
      // chaque tentative avec le même token) et on NE jette PAS non plus.
      // L'UI doit rediriger vers la reconnexion ; la photo reste en
      // mémoire côté écran pour permettre un nouvel envoi juste après.
      return SoumissionResult(
        ResultatSoumission.sessionExpiree,
        messageErreur: e.message,
      );
    } on ApiRejectedException catch (e) {
      // Erreur métier définitive (ex: doublon détecté) -> on ne remet PAS
      // en file, ça resterait rejeté indéfiniment.
      return SoumissionResult(
        ResultatSoumission.rejete,
        messageErreur: e.message,
      );
    } on ApiNetworkException catch (_) {
      // Pas de réseau utile OU erreur serveur transitoire (5xx) -> mise en
      // file, sera renvoyé automatiquement par SyncService dès que la
      // connexion (ou le serveur) redevient disponible.
      await _queueService.ajouter(signalement);
      _notifierEnAttente();
      return SoumissionResult(ResultatSoumission.misEnAttente);
    }
  }

  /// Rejoue tous les signalements en attente. Appelé par SyncService
  /// dès qu'une connexion revient, mais peut aussi être déclenché
  /// manuellement par l'utilisateur (ex: bouton "réessayer").
  Future<void> synchroniserFileAttente() async {
    final connectivite = await Connectivity().checkConnectivity();
    if (connectivite.contains(ConnectivityResult.none)) {
      return;
    }

    final enAttente = _queueService.listerTout();
    for (final signalement in enAttente) {
      try {
        await _apiService.envoyerSignalement(signalement, token: _obtenirToken());
        await _queueService.retirer(signalement.id);
      } on ApiRejectedException {
        // Rejeté définitivement (ex: doublon) -> on le retire pour ne pas
        // boucler dessus indéfiniment. À affiner plus tard si besoin de
        // notifier l'utilisateur de ce rejet a posteriori.
        await _queueService.retirer(signalement.id);
      } on ApiAuthException {
        // Token expiré pendant une resync en tâche de fond : on ne peut
        // rien envoyer tant que l'utilisateur ne s'est pas reconnecté.
        // On garde les éléments en file et on arrête cette passe.
        break;
      } on ApiNetworkException {
        // Toujours pas de réseau utile, ou erreur serveur transitoire ->
        // on arrête cette passe, on réessaiera au prochain déclenchement.
        break;
      }
    }
    _notifierEnAttente();
  }

  int get nombreEnAttente => _queueService.nombreEnAttente;

  void dispose() {
    _syncController.close();
  }
}