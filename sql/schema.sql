-- ============================================================
-- CoDeCI - Schéma de base de données
-- PostgreSQL 15+ avec extension PostGIS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- Entreprises de collecte (Éco Éburnie, ECOTI SA, etc.)
-- Créée avant "communes" car chaque commune référence directement
-- son opérateur attitré (correspond à la réalité du terrain : une
-- commune = un seul opérateur sous délégation de service public).
-- ============================================================
CREATE TABLE entreprises_collecte (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(150) NOT NULL,
    zones_assignees GEOGRAPHY(MULTIPOLYGON, 4326),  -- réservé pour un découpage plus fin, futur
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_entreprises_zones ON entreprises_collecte USING GIST (zones_assignees);

-- ============================================================
-- Communes (périmètres géographiques pour le contrôle d'accès)
-- ============================================================
CREATE TABLE communes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(120) NOT NULL,
    zone_geo GEOGRAPHY(POLYGON, 4326) NOT NULL,
    -- Nullable : certaines communes hors Abidjan n'ont pas encore
    -- d'opérateur privé référencé dans le système.
    entreprise_collecte_id UUID REFERENCES entreprises_collecte(id),
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_communes_zone_geo ON communes USING GIST (zone_geo);
CREATE INDEX idx_communes_entreprise ON communes (entreprise_collecte_id);

-- ============================================================
-- Utilisateurs
-- ============================================================
CREATE TYPE profil_utilisateur AS ENUM (
    'citoyen', 'chauffeur', 'agent_municipal', 'entreprise', 'admin', 'ministere'
);

CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(150) NOT NULL,
    telephone VARCHAR(20) NOT NULL UNIQUE,
    profil profil_utilisateur NOT NULL,
    commune_id UUID REFERENCES communes(id),
    entreprise_id UUID REFERENCES entreprises_collecte(id),
    solde_points INTEGER NOT NULL DEFAULT 0,
    actif BOOLEAN NOT NULL DEFAULT true,
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_utilisateurs_telephone ON utilisateurs (telephone);
CREATE INDEX idx_utilisateurs_profil ON utilisateurs (profil);

-- ============================================================
-- Camions
-- ============================================================
CREATE TYPE statut_camion AS ENUM ('actif', 'maintenance', 'inactif');

CREATE TABLE camions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    matricule VARCHAR(30) NOT NULL UNIQUE,
    entreprise_id UUID NOT NULL REFERENCES entreprises_collecte(id),
    statut statut_camion NOT NULL DEFAULT 'actif',
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Bacs publics
-- ============================================================
CREATE TYPE statut_bac AS ENUM ('vide', 'moyen', 'plein');

CREATE TABLE bacs_publics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    localisation GEOGRAPHY(POINT, 4326) NOT NULL,
    commune_id UUID NOT NULL REFERENCES communes(id),
    statut statut_bac NOT NULL DEFAULT 'moyen',
    derniere_vidange TIMESTAMPTZ,
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bacs_localisation ON bacs_publics USING GIST (localisation);

-- ============================================================
-- Catégories de signalement (table, pas enum figé -> évolutif)
-- ============================================================
CREATE TABLE categories_signalement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    libelle VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);

-- ============================================================
-- Photos (cycle de vie / rétention géré ici)
-- ============================================================
CREATE TYPE statut_verification_photo AS ENUM ('en_attente', 'valide', 'suspecte', 'rejetee');

CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_fichier TEXT,                          -- NULL après suppression post-rétention
    hash_perceptuel VARCHAR(64) NOT NULL,       -- conservé indéfiniment (anti-doublon)
    exif_gps GEOGRAPHY(POINT, 4326),
    exif_date TIMESTAMPTZ,
    statut_verification statut_verification_photo NOT NULL DEFAULT 'en_attente',
    motif_rejet TEXT,
    date_upload TIMESTAMPTZ NOT NULL DEFAULT now(),
    date_suppression_fichier TIMESTAMPTZ
);
CREATE INDEX idx_photos_hash ON photos (hash_perceptuel);

-- ============================================================
-- Signalements
-- ============================================================
CREATE TYPE statut_signalement AS ENUM ('en_attente', 'en_cours', 'resolu', 'rejete_fraude');
CREATE TYPE mode_soumission AS ENUM ('en_ligne', 'hors_ligne');

CREATE TABLE signalements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID NOT NULL REFERENCES utilisateurs(id),
    categorie_id UUID NOT NULL REFERENCES categories_signalement(id),
    bac_id UUID REFERENCES bacs_publics(id),
    coordonnees_gps GEOGRAPHY(POINT, 4326) NOT NULL,
    photo_id UUID NOT NULL REFERENCES photos(id),
    statut statut_signalement NOT NULL DEFAULT 'en_attente',
    mode_soumission mode_soumission NOT NULL DEFAULT 'en_ligne',
    commune_id UUID NOT NULL REFERENCES communes(id),
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now(),
    date_resolution TIMESTAMPTZ
);
CREATE INDEX idx_signalements_gps ON signalements USING GIST (coordonnees_gps);
CREATE INDEX idx_signalements_statut ON signalements (statut);
CREATE INDEX idx_signalements_commune ON signalements (commune_id);

-- ============================================================
-- Trajets camions
-- ============================================================
CREATE TYPE statut_trajet AS ENUM ('planifie', 'en_cours', 'termine');

CREATE TABLE trajets_camions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chauffeur_id UUID NOT NULL REFERENCES utilisateurs(id),
    camion_id UUID NOT NULL REFERENCES camions(id),
    liste_points_gps JSONB NOT NULL,            -- ordre calculé par OR-Tools
    ordre_modifie_manuellement BOOLEAN NOT NULL DEFAULT false,
    date_trajet DATE NOT NULL,
    statut statut_trajet NOT NULL DEFAULT 'planifie',
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trajets_chauffeur ON trajets_camions (chauffeur_id);
CREATE INDEX idx_trajets_date ON trajets_camions (date_trajet);

-- ============================================================
-- Points sautés (alertes automatiques)
-- ============================================================
CREATE TABLE points_sautes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trajet_id UUID NOT NULL REFERENCES trajets_camions(id),
    bac_id UUID NOT NULL REFERENCES bacs_publics(id),
    chauffeur_id UUID NOT NULL REFERENCES utilisateurs(id),
    alerte_envoyee BOOLEAN NOT NULL DEFAULT false,
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Transactions de points (programme de récompenses)
-- ============================================================
CREATE TYPE type_transaction_points AS ENUM (
    'gain_signalement', 'gain_tri_selectif', 'conversion_mobile_money'
);

CREATE TABLE transactions_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID NOT NULL REFERENCES utilisateurs(id),
    signalement_id UUID REFERENCES signalements(id),
    points INTEGER NOT NULL,
    type type_transaction_points NOT NULL,
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_transactions_utilisateur ON transactions_points (utilisateur_id);
