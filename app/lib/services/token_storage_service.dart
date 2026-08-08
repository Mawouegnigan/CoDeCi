import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Stockage chiffré du token JWT sur l'appareil.
///
/// Isolé dans son propre service pour que le reste de l'app (Repository,
/// écrans) n'ait jamais à connaître le mécanisme de stockage utilisé —
/// on pourrait le remplacer sans toucher à autre chose.
class TokenStorageService {
  static const _cleToken = 'codeci_access_token';

  final _storage = const FlutterSecureStorage();

  Future<void> enregistrerToken(String token) async {
    await _storage.write(key: _cleToken, value: token);
  }

  Future<String?> lireToken() async {
    return _storage.read(key: _cleToken);
  }

  Future<void> supprimerToken() async {
    await _storage.delete(key: _cleToken);
  }
}