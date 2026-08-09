import 'package:flutter/material.dart';

import '../../models/trajet.dart';
import '../../repositories/auth_repository.dart';
import '../../services/trajet_api_service.dart';

class TourneeScreen extends StatefulWidget {
  final AuthRepository authRepository;

  const TourneeScreen({super.key, required this.authRepository});

  @override
  State<TourneeScreen> createState() => _TourneeScreenState();
}

class _TourneeScreenState extends State<TourneeScreen> {
  final _apiService = TrajetApiService();

  bool _chargement = true;
  String? _erreur;
  Trajet? _trajet;

  @override
  void initState() {
    super.initState();
    _chargerTournee();
  }

  Future<void> _chargerTournee() async {
    setState(() {
      _chargement = true;
      _erreur = null;
    });

    final token = widget.authRepository.token;
    if (token == null) {
      setState(() {
        _erreur = 'Session invalide, reconnecte-toi.';
        _chargement = false;
      });
      return;
    }

    try {
      final trajet = await _apiService.tourneeDuJour(token);
      setState(() {
        _trajet = trajet;
        _chargement = false;
      });
    } on AucuneTourneeException {
      setState(() {
        _erreur = "Aucune tournée planifiée pour aujourd'hui.";
        _chargement = false;
      });
    } catch (e) {
      setState(() {
        _erreur = 'Impossible de charger la tournée. Vérifie ta connexion.';
        _chargement = false;
      });
    }
  }

  Color _couleurStatut(String? statut) {
    switch (statut) {
      case 'plein':
        return Colors.red;
      case 'moyen':
        return Colors.orange;
      case 'vide':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ma tournée du jour'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _chargerTournee,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _chargerTournee,
        child: _construireCorps(),
      ),
    );
  }

  Widget _construireCorps() {
    if (_chargement) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_erreur != null) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Icon(Icons.info_outline, size: 48, color: Colors.grey[500]),
          const SizedBox(height: 12),
          Text(
            _erreur!,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          Center(
            child: ElevatedButton(
              onPressed: _chargerTournee,
              child: const Text('Réessayer'),
            ),
          ),
        ],
      );
    }

    final trajet = _trajet!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.local_shipping, size: 32, color: Colors.orange),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Camion ${trajet.camionMatricule}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      Text(
                        '${trajet.points.length} bacs à collecter · ${trajet.statut}',
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        ...trajet.points.map((point) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: _couleurStatut(point.statutBac),
                  child: Text(
                    '${point.ordre}',
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
                title: Text('Bac #${point.ordre}'),
                subtitle: Text(
                  'Statut : ${point.statutBac ?? 'inconnu'}\n'
                  '${point.latitude.toStringAsFixed(6)}, ${point.longitude.toStringAsFixed(6)}',
                ),
                isThreeLine: true,
              ),
            )),
      ],
    );
  }
}