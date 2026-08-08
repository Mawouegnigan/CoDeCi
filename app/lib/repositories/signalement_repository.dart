import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../models/signalement.dart';
import '../services/api_service.dart';
import '../services/queue_service.dart';

/// Résultat renvoyé à l'UI après une tentative de soumission,
/// pour lui permettre d'afficher le bon message sans connaître
/// les détails de l'implémentation réseau.
enum ResultatSoumission { envoye, misEnAttente, rejete }

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
    } on ApiRejectedException catch (e) {
      // Erreur métier (ex: doublon détecté) -> on ne remet PAS en file,
      // ça resterait rejeté indéfiniment. On remonte l'erreur telle quelle.
      return SoumissionResult(
        ResultatSoumission.rejete,
        messageErreur: e.message,
      );
    } on ApiNetworkException catch (_) {
      // Pas de réseau utile -> mise en file, sera renvoyé automatiquement
      // par SyncService dès que la connexion revient.
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
      } on ApiNetworkException {
        // Toujours pas de réseau utile -> on arrête cette passe,
        // on réessaiera au prochain changement de connectivité.
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