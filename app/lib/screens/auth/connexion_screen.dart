import 'package:flutter/material.dart';

import '../../repositories/auth_repository.dart';
import '../../services/auth_api_service.dart';
import 'inscription_screen.dart';

class ConnexionScreen extends StatefulWidget {
  final AuthRepository authRepository;

  const ConnexionScreen({super.key, required this.authRepository});

  @override
  State<ConnexionScreen> createState() => _ConnexionScreenState();
}

class _ConnexionScreenState extends State<ConnexionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _telephoneController = TextEditingController();
  final _motDePasseController = TextEditingController();

  bool _chargement = false;
  String? _erreur;

  @override
  void dispose() {
    _telephoneController.dispose();
    _motDePasseController.dispose();
    super.dispose();
  }

  Future<void> _seConnecter() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _chargement = true;
      _erreur = null;
    });

    try {
      await widget.authRepository.connexion(
        telephone: _telephoneController.text.trim(),
        motDePasse: _motDePasseController.text,
      );
      // Pas besoin de navigation manuelle ici : l'écran racine de l'app
      // écoute authRepository.utilisateurStream et bascule automatiquement
      // vers l'écran principal dès que la connexion réussit.
    } on ApiAuthException catch (e) {
      setState(() => _erreur = e.message);
    } catch (_) {
      setState(() => _erreur = 'Impossible de se connecter. Vérifie ta connexion internet.');
    } finally {
      if (mounted) setState(() => _chargement = false);
    }
  }

  void _allerVersInscription() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => InscriptionScreen(authRepository: widget.authRepository),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: ListView(
              children: [
                const SizedBox(height: 48),
                const Icon(Icons.recycling, size: 64, color: Colors.orange),
                const SizedBox(height: 16),
                const Text(
                  'CoDeCI',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                ),
                const Text(
                  'Connecte-toi pour signaler et gagner des points',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _telephoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Numéro de téléphone',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.phone),
                  ),
                  validator: (valeur) {
                    if (valeur == null || valeur.trim().length < 8) {
                      return 'Numéro de téléphone invalide.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _motDePasseController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Mot de passe',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.lock),
                  ),
                  validator: (valeur) {
                    if (valeur == null || valeur.length < 8) {
                      return 'Le mot de passe doit faire au moins 8 caractères.';
                    }
                    return null;
                  },
                ),
                if (_erreur != null) ...[
                  const SizedBox(height: 12),
                  Text(_erreur!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _chargement ? null : _seConnecter,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: _chargement
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Se connecter'),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: _allerVersInscription,
                  child: const Text("Pas encore de compte ? S'inscrire"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}