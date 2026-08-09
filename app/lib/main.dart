import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'models/utilisateur.dart';
import 'repositories/auth_repository.dart';
import 'repositories/signalement_repository.dart';
import 'screens/auth/connexion_screen.dart';
import 'screens/signalement_screen.dart';
import 'services/sync_service.dart';
import 'screens/chauffeur/tournee_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();

  final authRepository = AuthRepository();
  await authRepository.restaurerSession();

  final signalementRepository = SignalementRepository(
    obtenirToken: () => authRepository.token,
  );
  await signalementRepository.init();

  final syncService = SyncService(signalementRepository);
  syncService.demarrer();

  runApp(CoDeCiApp(
    authRepository: authRepository,
    signalementRepository: signalementRepository,
  ));
}

class CoDeCiApp extends StatelessWidget {
  final AuthRepository authRepository;
  final SignalementRepository signalementRepository;

  const CoDeCiApp({
    super.key,
    required this.authRepository,
    required this.signalementRepository,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CoDeCI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.orange,
        useMaterial3: true,
      ),
      home: _EcranRacine(
        authRepository: authRepository,
        signalementRepository: signalementRepository,
      ),
    );
  }
}

/// Bascule automatiquement entre l'écran de connexion et l'écran principal
/// selon l'état de la session, en écoutant authRepository.utilisateurStream.
/// Aucun écran n'a besoin de gérer lui-même la navigation post-connexion
/// ou post-déconnexion : ça se fait ici, à un seul endroit.
class _EcranRacine extends StatelessWidget {
  final AuthRepository authRepository;
  final SignalementRepository signalementRepository;

  const _EcranRacine({
    required this.authRepository,
    required this.signalementRepository,
  });

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<UtilisateurConnecte?>(
      stream: authRepository.utilisateurStream,
      initialData: authRepository.utilisateurCourant,
      builder: (context, snapshot) {
        final utilisateur = snapshot.data;

        if (utilisateur == null) {
          return ConnexionScreen(authRepository: authRepository);
        }

        if (utilisateur.profil == 'chauffeur') {
          return TourneeScreen(authRepository: authRepository);
        }

        return SignalementScreen(
          repository: signalementRepository,
          authRepository: authRepository,
        );
      },
    );
  }
}