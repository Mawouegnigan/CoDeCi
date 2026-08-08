import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/utilisateur.dart';

class ApiAuthException implements Exception {
  final String message;
  ApiAuthException(this.message);
  @override
  String toString() => 'ApiAuthException: $message';
}

/// Couche responsable UNIQUEMENT de parler aux routes /auth/* du backend.
/// Ne gère ni le stockage du token, ni l'état de connexion : ça, c'est
/// le rôle d'AuthRepository.
class AuthApiService {
  Uri _uri(String chemin) => Uri.parse('${AppConfig.apiBaseUrl}$chemin');

  Future<({String token, UtilisateurConnecte utilisateur})> inscription({
    required String nom,
    required String telephone,
    required String motDePasse,
  }) async {
    final reponse = await http
        .post(
          _uri('/auth/inscription'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'nom': nom,
            'telephone': telephone,
            'mot_de_passe': motDePasse,
            // L'inscription publique ne crée jamais que des comptes citoyen.
            // Les autres profils (chauffeur, entreprise, admin...) sont créés
            // par un administrateur, jamais depuis cet écran.
            'profil': 'citoyen',
          }),
        )
        .timeout(AppConfig.apiTimeout);

    return _traiterReponseAuth(reponse, contexteErreurParDefaut:
        'Impossible de créer le compte. Vérifie tes informations.');
  }

  Future<({String token, UtilisateurConnecte utilisateur})> connexion({
    required String telephone,
    required String motDePasse,
  }) async {
    final reponse = await http
        .post(
          _uri('/auth/connexion'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'telephone': telephone,
            'mot_de_passe': motDePasse,
          }),
        )
        .timeout(AppConfig.apiTimeout);

    return _traiterReponseAuth(reponse, contexteErreurParDefaut:
        'Numéro de téléphone ou mot de passe incorrect.');
  }

  Future<UtilisateurConnecte> profilCourant(String token) async {
    final reponse = await http.get(
      _uri('/auth/moi'),
      headers: {'Authorization': 'Bearer $token'},
    ).timeout(AppConfig.apiTimeout);

    if (reponse.statusCode == 200) {
      return UtilisateurConnecte.fromJson(jsonDecode(reponse.body));
    }
    throw ApiAuthException('Session expirée, reconnecte-toi.');
  }

  ({String token, UtilisateurConnecte utilisateur}) _traiterReponseAuth(
    http.Response reponse, {
    required String contexteErreurParDefaut,
  }) {
    if (reponse.statusCode == 200 || reponse.statusCode == 201) {
      final corps = jsonDecode(reponse.body) as Map<String, dynamic>;
      return (
        token: corps['access_token'] as String,
        utilisateur: UtilisateurConnecte.fromJson(
          corps['utilisateur'] as Map<String, dynamic>,
        ),
      );
    }

    // Tente de récupérer le message d'erreur précis renvoyé par l'API
    // (ex: "Ce numéro est déjà associé à un compte."), sinon message générique.
    String? messagePrecis;
    try {
      final corps = jsonDecode(reponse.body) as Map<String, dynamic>;
      messagePrecis = corps['detail'] as String?;
    } catch (_) {
      // Corps de réponse non-JSON (ex: 500 brut) -> on garde messagePrecis à null.
    }
    throw ApiAuthException(messagePrecis ?? contexteErreurParDefaut);
  }
}