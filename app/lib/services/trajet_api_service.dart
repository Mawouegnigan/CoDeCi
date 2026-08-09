import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/trajet.dart';
import 'auth_api_service.dart';

/// Exception levée quand aucune tournée n'est planifiée pour aujourd'hui (404).
class AucuneTourneeException implements Exception {
  @override
  String toString() => "Aucune tournée planifiée pour aujourd'hui.";
}

/// Couche responsable UNIQUEMENT de parler à l'endpoint /trajets/aujourdhui.
class TrajetApiService {
  Future<Trajet> tourneeDuJour(String token) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}${AppConfig.trajetsEndpoint}',
    );

    try {
      final response = await http
          .get(uri, headers: {'Authorization': 'Bearer $token'})
          .timeout(AppConfig.apiTimeout);

      if (response.statusCode == 200) {
        return Trajet.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      }

      if (response.statusCode == 401 || response.statusCode == 403) {
        throw ApiAuthException('Session expirée, reconnecte-toi.');
      }

      if (response.statusCode == 404) {
        throw AucuneTourneeException();
      }

      throw ApiAuthException('Erreur inattendue (${response.statusCode}).');
    } on SocketException catch (e) {
      throw ApiAuthException('Pas de connexion : ${e.message}');
    } on HttpException catch (e) {
      throw ApiAuthException('Erreur réseau : ${e.message}');
    } on ApiAuthException {
      rethrow;
    } on AucuneTourneeException {
      rethrow;
    } catch (e) {
      throw ApiAuthException('Impossible de récupérer la tournée : $e');
    }
  }
}