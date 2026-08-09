-- Données de test pour le module chauffeur : un chauffeur, un camion,
-- 3 bacs publics à Cocody, et une tournée du jour reliant le tout.
--
-- Identifiants de test créés :
--   Téléphone : 0700000099
--   Mot de passe : chauffeur123

-- 1. Compte utilisateur chauffeur (rattaché à ECOTI SA)
INSERT INTO utilisateurs (id, nom, telephone, profil, entreprise_id, mot_de_passe_hash, solde_points, actif)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'Chauffeur Test',
    '0700000099',
    'chauffeur',
    'a0000000-0000-0000-0000-000000000001',
    '$2b$12$M8c1cZ39OumDK64km0/0QuOyna/9MdG69IQSKhI8V/p9bwBnH5DNm',
    0,
    true
);

-- 2. Camion assigné à ECOTI SA
INSERT INTO camions (id, matricule, entreprise_id, statut)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'CI-TEST-001',
    'a0000000-0000-0000-0000-000000000001',
    'actif'
);

-- 3. Trois bacs publics à Cocody
INSERT INTO bacs_publics (id, localisation, commune_id, statut)
VALUES
    ('d0000000-0000-0000-0000-000000000001', ST_GeogFromText('SRID=4326;POINT(-4.008256 5.359952)'), '657a9e9a-eaec-4e52-8187-e8650f9bb02b', 'plein'),
    ('d0000000-0000-0000-0000-000000000002', ST_GeogFromText('SRID=4326;POINT(-4.005000 5.362000)'), '657a9e9a-eaec-4e52-8187-e8650f9bb02b', 'moyen'),
    ('d0000000-0000-0000-0000-000000000003', ST_GeogFromText('SRID=4326;POINT(-4.011000 5.358000)'), '657a9e9a-eaec-4e52-8187-e8650f9bb02b', 'plein');

-- 4. Tournée du jour reliant le chauffeur, le camion et les 3 bacs
INSERT INTO trajets_camions (id, chauffeur_id, camion_id, liste_points_gps, date_trajet, statut)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    '[
        {"bac_id": "d0000000-0000-0000-0000-000000000001", "latitude": 5.359952, "longitude": -4.008256, "ordre": 1},
        {"bac_id": "d0000000-0000-0000-0000-000000000002", "latitude": 5.362000, "longitude": -4.005000, "ordre": 2},
        {"bac_id": "d0000000-0000-0000-0000-000000000003", "latitude": 5.358000, "longitude": -4.011000, "ordre": 3}
    ]'::jsonb,
    CURRENT_DATE,
    'planifie'
);