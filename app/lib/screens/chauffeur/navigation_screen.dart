import 'dart:async';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:mapbox_maps_flutter/mapbox_maps_flutter.dart' as mb;

import '../../models/trajet.dart';
import '../../repositories/auth_repository.dart';
import '../../services/navigation_api_service.dart';
import '../../services/trajet_api_service.dart';

class NavigationScreen extends StatefulWidget {
  final AuthRepository authRepository;
  final Trajet trajet;
  final PointTrajet pointCible;

  const NavigationScreen({
    super.key,
    required this.authRepository,
    required this.trajet,
    required this.pointCible,
  });

  @override
  State<NavigationScreen> createState() => _NavigationScreenState();
}

class _NavigationScreenState extends State<NavigationScreen> {
  final _navigationApiService = NavigationApiService();
  final _trajetApiService = TrajetApiService();

  mb.MapboxMap? _mapboxMap;
  mb.PolylineAnnotationManager? _polylineManager;

  StreamSubscription<Position>? _abonnementPosition;
  Position? _positionActuelle;

  ItineraireResultat? _itineraire;
  bool _chargementItineraire = true;
  bool _collecteEnCours = false;
  String? _erreur;

  @override
  void initState() {
    super.initState();
    _demarrerSuiviPosition();
  }

  @override
  void dispose() {
    _abonnementPosition?.cancel();
    super.dispose();
  }

  Future<void> _demarrerSuiviPosition() async {
    final serviceActif = await Geolocator.isLocationServiceEnabled();
    if (!serviceActif) {
      setState(() {
        _erreur = 'Active la localisation pour naviguer.';
        _chargementItineraire = false;
      });
      return;
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        setState(() {
          _erreur = 'Autorisation de localisation refusée.';
          _chargementItineraire = false;
        });
        return;
      }
    }
    if (permission == LocationPermission.deniedForever) {
      setState(() {
        _erreur = 'Autorisation de localisation bloquée. Active-la dans les réglages.';
        _chargementItineraire = false;
      });
      return;
    }

    // Première position : sert à calculer l'itinéraire initial.
    final position = await Geolocator.getCurrentPosition();
    setState(() => _positionActuelle = position);
    await _chargerItineraire(position);

    // Suivi continu : met à jour le point bleu sur la carte à chaque
    // déplacement significatif (10 m), sans recalculer l'itinéraire
    // automatiquement (pas de re-routing auto en cas de déviation pour
    // ce MVP, voir bouton "Recalculer" manuel).
    _abonnementPosition = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
      ),
    ).listen((position) {
      setState(() => _positionActuelle = position);
    });
  }

  Future<void> _chargerItineraire(Position depart) async {
    setState(() {
      _chargementItineraire = true;
      _erreur = null;
    });

    try {
      final itineraire = await _navigationApiService.obtenirItineraire(
        departLatitude: depart.latitude,
        departLongitude: depart.longitude,
        arriveeLatitude: widget.pointCible.latitude,
        arriveeLongitude: widget.pointCible.longitude,
      );
      setState(() {
        _itineraire = itineraire;
        _chargementItineraire = false;
      });
      await _dessinerTrace(itineraire);
      await _centrerCameraSurTrace(itineraire);
    } on ErreurNavigation catch (e) {
      setState(() {
        _erreur = e.message;
        _chargementItineraire = false;
      });
    }
  }

  Future<void> _dessinerTrace(ItineraireResultat itineraire) async {
    final manager = _polylineManager;
    if (manager == null) return;

    await manager.deleteAll();

    final points = itineraire.geometrie
        .map((p) => mb.Position(p[0], p[1]))
        .toList();

    await manager.create(
      mb.PolylineAnnotationOptions(
        geometry: mb.LineString(coordinates: points),
        lineColor: 0xFFFF8C00, // orange, cohérent avec le thème de l'app
        lineWidth: 5.0,
      ),
    );
  }

  Future<void> _centrerCameraSurTrace(ItineraireResultat itineraire) async {
    final map = _mapboxMap;
    if (map == null || itineraire.geometrie.isEmpty) return;

    final coordonnees =
        itineraire.geometrie.map((p) => mb.Position(p[0], p[1])).toList();

    final camera = await map.cameraForCoordinates(
      coordonnees.map((c) => mb.Point(coordinates: c)).toList(),
      mb.MbxEdgeInsets(top: 100, left: 40, bottom: 200, right: 40),
      null,
      null,
    );
    await map.flyTo(camera, mb.MapAnimationOptions(duration: 800));
  }

  Future<void> _onMapCreated(mb.MapboxMap mapboxMap) async {
    _mapboxMap = mapboxMap;
    await mapboxMap.location.updateSettings(
      mb.LocationComponentSettings(enabled: true, pulsingEnabled: true),
    );
    _polylineManager = await mapboxMap.annotations.createPolylineAnnotationManager();

    if (_itineraire != null) {
      await _dessinerTrace(_itineraire!);
      await _centrerCameraSurTrace(_itineraire!);
    }
  }

  Future<void> _recalculerItineraire() async {
    final position = _positionActuelle;
    if (position == null) return;
    await _chargerItineraire(position);
  }

  Future<void> _marquerBacCollecte() async {
    final token = widget.authRepository.token;
    if (token == null) return;

    setState(() => _collecteEnCours = true);

    try {
      await _trajetApiService.collecterBac(
        token: token,
        trajetId: widget.trajet.id,
        bacId: widget.pointCible.bacId,
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      setState(() => _collecteEnCours = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Impossible de marquer ce bac. Réessaie.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  String _formaterDistance(double metres) {
    if (metres < 1000) return '${metres.round()} m';
    return '${(metres / 1000).toStringAsFixed(1)} km';
  }

  String _formaterDuree(double secondes) {
    final minutes = (secondes / 60).round();
    if (minutes < 1) return '< 1 min';
    return '$minutes min';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Vers le bac #${widget.pointCible.ordre}'),
      ),
      body: Stack(
        children: [
          mb.MapWidget(
            onMapCreated: _onMapCreated,
            cameraOptions: mb.CameraOptions(
              center: mb.Point(
                coordinates: mb.Position(
                  widget.pointCible.longitude,
                  widget.pointCible.latitude,
                ),
              ),
              zoom: 14,
            ),
          ),
          if (_erreur != null)
            Positioned(
              top: 16,
              left: 16,
              right: 16,
              child: Card(
                color: Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(_erreur!, style: const TextStyle(color: Colors.red)),
                ),
              ),
            ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Card(
              margin: EdgeInsets.zero,
              shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_chargementItineraire)
                      const Center(child: CircularProgressIndicator())
                    else if (_itineraire != null) ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _formaterDistance(_itineraire!.distanceMetres),
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            _formaterDuree(_itineraire!.dureeSecondes),
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          TextButton.icon(
                            onPressed: _recalculerItineraire,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Recalculer'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                    ],
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _collecteEnCours ? null : _marquerBacCollecte,
                        child: _collecteEnCours
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Text('Bac collecté'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}