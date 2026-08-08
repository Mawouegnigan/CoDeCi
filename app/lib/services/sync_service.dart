import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../repositories/signalement_repository.dart';

/// Écoute les changements de connectivité et relance automatiquement
/// l'envoi des signalements en attente dès que le réseau revient.
///
/// À démarrer une seule fois au lancement de l'app (voir main.dart).
class SyncService {
  final SignalementRepository _repository;
  StreamSubscription<List<ConnectivityResult>>? _subscription;

  SyncService(this._repository);

  void demarrer() {
    // Tentative immédiate au démarrage, au cas où des signalements
    // seraient déjà en attente d'une session précédente.
    _repository.synchroniserFileAttente();

    _subscription = Connectivity().onConnectivityChanged.listen((resultats) {
      final estConnecte = !resultats.contains(ConnectivityResult.none);
      if (estConnecte) {
        _repository.synchroniserFileAttente();
      }
    });
  }

  void arreter() {
    _subscription?.cancel();
  }
}