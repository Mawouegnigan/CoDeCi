import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/signalement.dart';

/// Exception levée quand l'envoi échoue pour une raison réseau OU pour une
/// erreur serveur transitoire (5xx) : dans les deux cas, retenter plus tard
/// a du sens, donc le Repository traite ce cas de la même façon (mise en file).
class ApiNetworkException implements Exception {
  final String message;
  ApiNetworkException(this.message);
  @override
  String toString() => 'ApiNetworkException: $message';
}

/// Exception levée quand l'API répond et rejette la requête de façon
/// définitive (ex: 422 doublon détecté par le service anti-fraude,
/// 400 payload invalide). Retenter ne changerait rien : pas de mise en file.
class ApiRejectedException implements Exception {
  final int statusCode;
  final String message;
  ApiRejectedException(this.statusCode, this.message);
  @override
  String toString() => 'ApiRejectedException($statusCode): $message';
}

/// Exception levée quand le token JWT est absent, invalide ou expiré (401).
/// Ce n'est pas un rejet du signalement : il faut renvoyer l'utilisateur
/// vers la reconnexion, pas jeter sa photo ni la mettre en file d'attente
/// indéfiniment (elle échouerait à chaque tentative avec le même token).
class ApiAuthException implements Exception {
  final String message;
  ApiAuthException(this.message);
  @override
  String toString() => 'ApiAuthException: $message';
}

/// Extrait le champ "detail" d'une réponse d'erreur FastAPI standard.
/// Si le corps n'est pas du JSON exploitable (ex: erreur 500 HTML d'un
/// proxy), on retombe sur le corps brut plutôt que de planter.
String _extraireDetail(String body) {
  try {
    final decode = jsonDecode(body);
    if (decode is Map && decode['detail'] != null) {
      return decode['detail'].toString();
    }
  } catch (_) {
    // Corps non-JSON : on garde le comportement de repli ci-dessous.
  }
  return body;
}

/// Couche responsable UNIQUEMENT de parler au backend.
/// Ne sait rien de la file d'attente locale : c'est le Repository qui gère ça.
class ApiService {
  Future<void> envoyerSignalement(
    Signalement signalement, {
    String? token,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}${AppConfig.signalementsEndpoint}',
    );

    try {
      final request = http.MultipartRequest('POST', uri)
        ..fields['latitude'] = signalement.latitude.toString()
        ..fields['longitude'] = signalement.longitude.toString()
        ..fields['categorie'] = signalement.categorie.apiValue
        ..fields['date_creation'] = signalement.dateCreation.toIso8601String();

      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      if (signalement.commentaire != null) {
        request.fields['commentaire'] = signalement.commentaire!;
      }

      request.files.add(
        http.MultipartFile.fromBytes(
          'photo',
          signalement.photoBytes,
          filename: signalement.photoFileName,
        ),
      );

      final streamedResponse =
          await request.send().timeout(AppConfig.apiTimeout);
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200 || response.statusCode == 201) {
        return;
      }

      if (response.statusCode == 401) {
        throw ApiAuthException(
          'Session expirée, merci de vous reconnecter.',
        );
      }

      if (response.statusCode >= 500) {
        // Erreur serveur transitoire : on la traite comme un problème
        // réseau pour que le Repository remette le signalement en file
        // au lieu de le perdre définitivement.
        throw ApiNetworkException(
          'Erreur serveur (${response.statusCode}), nouvelle tentative programmée.',
        );
      }

      // Rejet métier définitif (ex: 422 doublon anti-fraude, 400 invalide).
      // FastAPI renvoie {"detail": "..."} : on l'extrait pour afficher un
      // message propre à l'utilisateur plutôt que le JSON brut.
      throw ApiRejectedException(response.statusCode, _extraireDetail(response.body));
    } on SocketException catch (e) {
      throw ApiNetworkException(e.message);
    } on HttpException catch (e) {
      throw ApiNetworkException(e.message);
    } on ApiAuthException {
      rethrow;
    } on ApiRejectedException {
      rethrow;
    } on ApiNetworkException {
      rethrow;
    } catch (e) {
      // Timeout ou autre souci réseau -> traité comme "pas de connexion utile".
      throw ApiNetworkException(e.toString());
    }
  }
}