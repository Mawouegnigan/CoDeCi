import 'dart:async';

import '../models/utilisateur.dart';
import '../services/auth_api_service.dart';
import '../services/token_storage_service.dart';

/// Point d'entrée UNIQUE pour l'UI concernant l'authentification.
/// Gère le cycle de vie complet : inscription, connexion, déconnexion,
/// et restauration de session au démarrage de l'app.
class AuthRepository {
  final AuthApiService _apiService;
  final TokenStorageService _tokenStorage;

  final _utilisateurController =
      StreamController<UtilisateurConnecte?>.broadcast();

  /// Émet l'utilisateur connecté, ou null si personne n'est connecté.
  /// L'UI peut s'abonner à ce flux pour réagir automatiquement aux
  /// connexions/déconnexions sans logique supplémentaire.
  Stream<UtilisateurConnecte?> get utilisateurStream =>
      _utilisateurController.stream;

  UtilisateurConnecte? _utilisateurCourant;
  UtilisateurConnecte? get utilisateurCourant => _utilisateurCourant;

  String? _token;
  String? get token => _token;

  AuthRepository({
    AuthApiService? apiService,
    TokenStorageService? tokenStorage,
  })  : _apiService = apiService ?? AuthApiService(),
        _tokenStorage = tokenStorage ?? TokenStorageService();

  /// À appeler une fois au démarrage de l'app : tente de restaurer une
  /// session existante à partir du token stocké localement.
  Future<void> restaurerSession() async {
    final token = await _tokenStorage.lireToken();
    if (token == null) {
      _emettreUtilisateur(null);
      return;
    }

    try {
      final utilisateur = await _apiService.profilCourant(token);
      _token = token;
      _emettreUtilisateur(utilisateur);
    } on ApiAuthException {
      // Token expiré ou invalide -> on nettoie et on repart sur une
      // session déconnectée plutôt que de laisser un état incohérent.
      await _tokenStorage.supprimerToken();
      _emettreUtilisateur(null);
    }
  }

  Future<void> inscription({
    required String nom,
    required String telephone,
    required String motDePasse,
  }) async {
    final resultat = await _apiService.inscription(
      nom: nom,
      telephone: telephone,
      motDePasse: motDePasse,
    );
    await _connecterAvec(resultat.token, resultat.utilisateur);
  }

  Future<void> connexion({
    required String telephone,
    required String motDePasse,
  }) async {
    final resultat = await _apiService.connexion(
      telephone: telephone,
      motDePasse: motDePasse,
    );
    await _connecterAvec(resultat.token, resultat.utilisateur);
  }

  Future<void> deconnexion() async {
    await _tokenStorage.supprimerToken();
    _token = null;
    _emettreUtilisateur(null);
  }

  Future<void> _connecterAvec(String token, UtilisateurConnecte utilisateur) async {
    await _tokenStorage.enregistrerToken(token);
    _token = token;
    _emettreUtilisateur(utilisateur);
  }

  void _emettreUtilisateur(UtilisateurConnecte? utilisateur) {
    _utilisateurCourant = utilisateur;
    _utilisateurController.add(utilisateur);
  }

  void dispose() {
    _utilisateurController.close();
  }
}