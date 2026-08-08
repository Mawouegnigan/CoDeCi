import 'dart:io';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/signalement.dart';

/// Exception levée quand l'envoi échoue pour une raison réseau
/// (à distinguer d'une erreur métier renvoyée par l'API, ex: doublon 422).
class ApiNetworkException implements Exception {
  final String message;
  ApiNetworkException(this.message);
  @override
  String toString() => 'ApiNetworkException: $message';
}

/// Exception levée quand l'API répond mais rejette la requête
/// (ex: 422 doublon détecté par le service anti-fraude).
class ApiRejectedException implements Exception {
  final int statusCode;
  final String message;
  ApiRejectedException(this.statusCode, this.message);
  @override
  String toString() => 'ApiRejectedException($statusCode): $message';
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

      // Erreur métier (ex: 422 doublon anti-fraude) -> ne pas remettre en file,
      // c'est au Repository de décider quoi faire de cette info.
      throw ApiRejectedException(response.statusCode, response.body);
    } on SocketException catch (e) {
      throw ApiNetworkException(e.message);
    } on HttpException catch (e) {
      throw ApiNetworkException(e.message);
    } on ApiRejectedException {
      rethrow;
    } catch (e) {
      // Timeout ou autre souci réseau -> traité comme "pas de connexion utile".
      throw ApiNetworkException(e.toString());
    }
  }
}