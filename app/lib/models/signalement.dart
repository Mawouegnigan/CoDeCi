import 'dart:typed_data';

import 'package:uuid/uuid.dart';

/// Les 5 catégories validées dans le CDCF.
enum CategorieSignalement {
  depotSauvage,
  bacPlein,
  bacEndommage,
  dechetDangereux,
  dechetRecyclable,
}

extension CategorieSignalementLabel on CategorieSignalement {
  /// Valeur envoyée à l'API (doit correspondre aux valeurs attendues côté backend).
  String get apiValue {
    switch (this) {
      case CategorieSignalement.depotSauvage:
        return 'depot_sauvage';
      case CategorieSignalement.bacPlein:
        return 'bac_plein';
      case CategorieSignalement.bacEndommage:
        return 'bac_endommage';
      case CategorieSignalement.dechetDangereux:
        return 'dechet_dangereux';
      case CategorieSignalement.dechetRecyclable:
        return 'dechet_recyclable';
    }
  }

  /// Libellé affiché à l'utilisateur.
  String get label {
    switch (this) {
      case CategorieSignalement.depotSauvage:
        return 'Dépôt sauvage';
      case CategorieSignalement.bacPlein:
        return 'Bac plein';
      case CategorieSignalement.bacEndommage:
        return 'Bac endommagé';
      case CategorieSignalement.dechetDangereux:
        return 'Déchet dangereux';
      case CategorieSignalement.dechetRecyclable:
        return 'Déchet recyclable';
    }
  }
}

/// Statut local du signalement (ne concerne que le stockage sur le téléphone,
/// pas le statut métier renvoyé par le backend).
enum StatutLocal { enAttente, envoye }

/// Modèle de signalement citoyen.
///
/// Stocké tel quel (en Map) dans Hive quand il est mis en file d'attente,
/// donc on garde volontairement des types primitifs (String, double, int)
/// pour éviter d'avoir besoin d'un TypeAdapter généré par build_runner.
class Signalement {
  final String id;
  final Uint8List photoBytes;
  final String photoFileName;
  final double latitude;
  final double longitude;
  final CategorieSignalement categorie;
  final DateTime dateCreation;
  final String? commentaire;
  StatutLocal statut;

  Signalement({
    String? id,
    required this.photoBytes,
    this.photoFileName = 'photo.jpg',
    required this.latitude,
    required this.longitude,
    required this.categorie,
    DateTime? dateCreation,
    this.commentaire,
    this.statut = StatutLocal.enAttente,
  })  : id = id ?? const Uuid().v4(),
        dateCreation = dateCreation ?? DateTime.now();

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'photoBytes': photoBytes,
      'photoFileName': photoFileName,
      'latitude': latitude,
      'longitude': longitude,
      'categorie': categorie.name,
      'dateCreation': dateCreation.toIso8601String(),
      'commentaire': commentaire,
      'statut': statut.name,
    };
  }

  factory Signalement.fromMap(Map<dynamic, dynamic> map) {
    return Signalement(
      id: map['id'] as String,
      photoBytes: map['photoBytes'] as Uint8List,
      photoFileName: map['photoFileName'] as String? ?? 'photo.jpg',
      latitude: map['latitude'] as double,
      longitude: map['longitude'] as double,
      categorie: CategorieSignalement.values.firstWhere(
        (c) => c.name == map['categorie'],
      ),
      dateCreation: DateTime.parse(map['dateCreation'] as String),
      commentaire: map['commentaire'] as String?,
      statut: StatutLocal.values.firstWhere(
        (s) => s.name == map['statut'],
      ),
    );
  }
}