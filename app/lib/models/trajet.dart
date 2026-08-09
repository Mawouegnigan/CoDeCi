/// Un arrêt (bac) dans la tournée du chauffeur.
class PointTrajet {
  final String bacId;
  final double latitude;
  final double longitude;
  final int ordre;
  final String? statutBac;

  PointTrajet({
    required this.bacId,
    required this.latitude,
    required this.longitude,
    required this.ordre,
    this.statutBac,
  });

  factory PointTrajet.fromJson(Map<String, dynamic> json) {
    return PointTrajet(
      bacId: json['bac_id'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      ordre: json['ordre'] as int,
      statutBac: json['statut_bac'] as String?,
    );
  }
}

/// Tournée du jour d'un chauffeur, avec ses arrêts ordonnés.
class Trajet {
  final String id;
  final String dateTrajet;
  final String statut;
  final String camionMatricule;
  final List<PointTrajet> points;

  Trajet({
    required this.id,
    required this.dateTrajet,
    required this.statut,
    required this.camionMatricule,
    required this.points,
  });

  factory Trajet.fromJson(Map<String, dynamic> json) {
    return Trajet(
      id: json['id'] as String,
      dateTrajet: json['date_trajet'] as String,
      statut: json['statut'] as String,
      camionMatricule: json['camion_matricule'] as String,
      points: (json['points'] as List)
          .map((p) => PointTrajet.fromJson(p as Map<String, dynamic>))
          .toList(),
    );
  }
}