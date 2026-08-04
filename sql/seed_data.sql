-- ============================================================
-- CoDeCI - Données de départ (seed)
-- Source : répartition officielle des opérateurs de collecte à
-- Abidjan sous délégation de service public, supervisée par
-- l'ANAGED (situation vérifiée en 2026).
--
-- IMPORTANT : les polygones "zone_geo" ci-dessous sont des
-- rectangles approximatifs (± ~2 km) centrés sur le cœur de
-- chaque commune, générés pour disposer de données de test
-- géographiquement plausibles. Ce ne sont PAS les limites
-- administratives officielles. À remplacer par les vraies
-- géométries (shapefiles de l'ANSTAT ou de l'INS) avant toute
-- utilisation en production -- la logique de filtrage par
-- périmètre (mairie / entreprise / national) fonctionne déjà
-- correctement avec ces données, seule la précision cartographique
-- devra être affinée plus tard.
-- ============================================================

-- ============================================================
-- 1. Entreprises de collecte (District Autonome d'Abidjan)
-- ============================================================
INSERT INTO entreprises_collecte (id, nom) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'ECOTI SA'),
    ('a0000000-0000-0000-0000-000000000002', 'ECO EBURNIE');

-- Note : un troisième opérateur, CLEAN EBURNIE, gère le Centre de
-- Valorisation et d'Enfouissement Technique (CVET) de Kossihouen
-- (traitement final, pas de collecte directe auprès des communes).
-- Non inclus ici : à intégrer si le périmètre du projet s'étend au
-- suivi du traitement/enfouissement.

-- ============================================================
-- 2. Communes du District Autonome d'Abidjan (13 communes)
-- Répartition réelle des opérateurs :
--   ECOTI SA     -> Cocody, Abobo, Anyama, Plateau, Bingerville
--   ECO EBURNIE  -> Adjamé, Attécoubé, Yopougon, Songon,
--                    Treichville, Marcory, Koumassi, Port-Bouët
-- ============================================================

-- ECOTI SA (secteur 1)
INSERT INTO communes (nom, zone_geo, entreprise_collecte_id) VALUES
    ('Cocody', ST_MakeEnvelope(-3.9950, 5.3399, -3.9550, 5.3799, 4326)::geography,
        'a0000000-0000-0000-0000-000000000001'),
    ('Abobo', ST_MakeEnvelope(-4.0370, 5.3970, -3.9970, 5.4370, 4326)::geography,
        'a0000000-0000-0000-0000-000000000001'),
    ('Anyama', ST_MakeEnvelope(-4.0711, 5.4739, -4.0311, 5.5139, 4326)::geography,
        'a0000000-0000-0000-0000-000000000001'),
    ('Plateau', ST_MakeEnvelope(-4.0427, 5.3002, -4.0027, 5.3402, 4326)::geography,
        'a0000000-0000-0000-0000-000000000001'),
    ('Bingerville', ST_MakeEnvelope(-3.9033, 5.3356, -3.8633, 5.3756, 4326)::geography,
        'a0000000-0000-0000-0000-000000000001');

-- ECO EBURNIE (secteurs 2 et 3)
INSERT INTO communes (nom, zone_geo, entreprise_collecte_id) VALUES
    ('Adjamé', ST_MakeEnvelope(-4.0442, 5.3358, -4.0042, 5.3758, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Attécoubé', ST_MakeEnvelope(-4.0533, 5.3133, -4.0133, 5.3533, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Yopougon', ST_MakeEnvelope(-4.1064, 5.3253, -4.0664, 5.3653, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Songon', ST_MakeEnvelope(-4.2867, 5.2967, -4.2467, 5.3367, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Treichville', ST_MakeEnvelope(-4.0286, 5.2672, -3.9886, 5.3072, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Marcory', ST_MakeEnvelope(-4.0020, 5.2726, -3.9620, 5.3126, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Koumassi', ST_MakeEnvelope(-3.9702, 5.2737, -3.9302, 5.3137, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002'),
    ('Port-Bouët', ST_MakeEnvelope(-3.9533, 5.2300, -3.9133, 5.2700, 4326)::geography,
        'a0000000-0000-0000-0000-000000000002');

-- ============================================================
-- 3. Catégories de signalement (validées dans le CDCF)
-- ============================================================
INSERT INTO categories_signalement (libelle, description) VALUES
    ('Dépôt sauvage', 'Amas de déchets abandonnés en dehors d''un point de collecte officiel'),
    ('Bac plein', 'Bac public de collecte arrivé à saturation'),
    ('Bac endommagé', 'Bac public cassé, renversé ou hors d''usage'),
    ('Déchet dangereux', 'Déchet potentiellement toxique ou dangereux (produits chimiques, médicaux, etc.)'),
    ('Déchet recyclable', 'Dépôt de déchets valorisables dans le cadre du tri sélectif (plastique, etc.)');
