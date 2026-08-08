/// Représentation de l'utilisateur connecté côté client,
/// miroir du schéma UtilisateurReponse renvoyé par l'API.
class UtilisateurConnecte {
  final String id;
  final String nom;
  final String telephone;
  final String profil;
  final int soldePoints;

  UtilisateurConnecte({
    required this.id,
    required this.nom,
    required this.telephone,
    required this.profil,
    required this.soldePoints,
  });

  factory UtilisateurConnecte.fromJson(Map<String, dynamic> json) {
    return UtilisateurConnecte(
      id: json['id'] as String,
      nom: json['nom'] as String,
      telephone: json['telephone'] as String,
      profil: json['profil'] as String,
      soldePoints: json['solde_points'] as int,
    );
  }
}