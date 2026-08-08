import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../models/signalement.dart';
import '../repositories/auth_repository.dart';
import '../repositories/signalement_repository.dart';

class SignalementScreen extends StatefulWidget {
  final SignalementRepository repository;
  final AuthRepository authRepository;

  const SignalementScreen({
    super.key,
    required this.repository,
    required this.authRepository,
  });

  @override
  State<SignalementScreen> createState() => _SignalementScreenState();
}

class _SignalementScreenState extends State<SignalementScreen> {
  final _picker = ImagePicker();

  Uint8List? _photoBytes;
  String _photoFileName = 'photo.jpg';
  Position? _position;
  CategorieSignalement? _categorie;
  bool _envoiEnCours = false;
  int _enAttente = 0;

  @override
  void initState() {
    super.initState();
    _enAttente = widget.repository.nombreEnAttente;
    widget.repository.enAttenteStream.listen((valeur) {
      if (mounted) setState(() => _enAttente = valeur);
    });
  }

  Future<void> _prendrePhoto() async {
    final photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );
    if (photo != null) {
      final bytes = await photo.readAsBytes();
      setState(() {
        _photoBytes = bytes;
        _photoFileName = photo.name;
      });
    }
  }

  Future<void> _recupererPosition() async {
    final serviceActif = await Geolocator.isLocationServiceEnabled();
    if (!serviceActif) {
      _afficherMessage('Active la localisation pour continuer.');
      return;
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        _afficherMessage('Autorisation de localisation refusée.');
        return;
      }
    }
    if (permission == LocationPermission.deniedForever) {
      _afficherMessage(
        'Autorisation de localisation bloquée. Active-la dans les réglages.',
      );
      return;
    }

    final position = await Geolocator.getCurrentPosition();
    setState(() => _position = position);
  }

  bool get _formulaireValide =>
      _photoBytes != null && _position != null && _categorie != null;

  Future<void> _soumettre() async {
    if (!_formulaireValide) {
      _afficherMessage('Photo, position et catégorie sont obligatoires.');
      return;
    }

    setState(() => _envoiEnCours = true);

    final signalement = Signalement(
      photoBytes: _photoBytes!,
      photoFileName: _photoFileName,
      latitude: _position!.latitude,
      longitude: _position!.longitude,
      categorie: _categorie!,
    );

    final resultat = await widget.repository.submitSignalement(signalement);

    setState(() => _envoiEnCours = false);

    switch (resultat.resultat) {
      case ResultatSoumission.envoye:
        _afficherMessage('Signalement envoyé avec succès.');
        _reinitialiserFormulaire();
        break;
      case ResultatSoumission.misEnAttente:
        _afficherMessage(
          'Pas de connexion : le signalement sera envoyé automatiquement '
          'dès que le réseau reviendra.',
        );
        _reinitialiserFormulaire();
        break;
      case ResultatSoumission.rejete:
        _afficherMessage(
          resultat.messageErreur ?? 'Signalement rejeté par le serveur.',
        );
        break;
    }
  }

  void _reinitialiserFormulaire() {
    setState(() {
      _photoBytes = null;
      _position = null;
      _categorie = null;
    });
  }

  void _afficherMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Signaler un déchet'),
        actions: [
          if (_enAttente > 0)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Chip(
                  label: Text('$_enAttente en attente'),
                  backgroundColor: Colors.orange.shade100,
                ),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Se déconnecter',
            onPressed: () => widget.authRepository.deconnexion(),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            _buildBlocPhoto(),
            const SizedBox(height: 16),
            _buildBlocPosition(),
            const SizedBox(height: 16),
            _buildBlocCategorie(),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _envoiEnCours ? null : _soumettre,
              child: _envoiEnCours
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Envoyer le signalement'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBlocPhoto() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Photo *', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (_photoBytes != null)
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.memory(
              _photoBytes!,
              height: 180,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
          ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _prendrePhoto,
          icon: const Icon(Icons.camera_alt),
          label: Text(_photoBytes == null ? 'Prendre une photo' : 'Reprendre'),
        ),
      ],
    );
  }

  Widget _buildBlocPosition() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Position *', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (_position != null)
          Text(
            'Lat: ${_position!.latitude.toStringAsFixed(5)}, '
            'Lng: ${_position!.longitude.toStringAsFixed(5)}',
          ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _recupererPosition,
          icon: const Icon(Icons.my_location),
          label: Text(_position == null ? 'Récupérer ma position' : 'Actualiser'),
        ),
      ],
    );
  }

  Widget _buildBlocCategorie() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Catégorie *', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        DropdownButtonFormField<CategorieSignalement>(
          value: _categorie,
          decoration: const InputDecoration(border: OutlineInputBorder()),
          hint: const Text('Choisir une catégorie'),
          items: CategorieSignalement.values
              .map((c) => DropdownMenuItem(value: c, child: Text(c.label)))
              .toList(),
          onChanged: (valeur) => setState(() => _categorie = valeur),
        ),
      ],
    );
  }
}