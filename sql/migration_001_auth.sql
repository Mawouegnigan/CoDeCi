-- Migration : ajout de l'authentification par mot de passe
-- À exécuter une seule fois sur la base codeci_db existante.
--
-- Utilisation :
--   psql -U postgres -d codeci_db -f sql/migration_001_auth.sql

ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS mot_de_passe_hash VARCHAR(255);

-- Note : la colonne est nullable pour ne pas casser les utilisateurs de test
-- déjà créés manuellement en SQL. En production, une fois tous les comptes
-- migrés vers un vrai mot de passe, on pourra passer la colonne en NOT NULL :
--   ALTER TABLE utilisateurs ALTER COLUMN mot_de_passe_hash SET NOT NULL;