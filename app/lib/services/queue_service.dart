import 'package:hive_flutter/hive_flutter.dart';

import '../models/signalement.dart';

/// Gère le stockage local des signalements en attente d'envoi.
///
/// Utilise Hive avec des Map<String, dynamic> brutes (pas de TypeAdapter
/// généré) : plus simple à maintenir, pas de build_runner à relancer
/// à chaque changement du modèle.
class QueueService {
  static const String _boxName = 'signalements_queue';

  Box? _box;

  Future<void> init() async {
    _box = await Hive.openBox(_boxName);
  }

  Box get _requireBox {
    final box = _box;
    if (box == null) {
      throw StateError(
        'QueueService.init() doit être appelé avant toute utilisation.',
      );
    }
    return box;
  }

  Future<void> ajouter(Signalement signalement) async {
    await _requireBox.put(signalement.id, signalement.toMap());
  }

  Future<void> retirer(String id) async {
    await _requireBox.delete(id);
  }

  List<Signalement> listerTout() {
    return _requireBox.values
        .map((raw) => Signalement.fromMap(raw as Map))
        .toList()
      ..sort((a, b) => a.dateCreation.compareTo(b.dateCreation));
  }

  int get nombreEnAttente => _requireBox.length;
}