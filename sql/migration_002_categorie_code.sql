-- Migration : ajout d'un code stable (sans accent) pour chaque catégorie
-- de signalement, utilisé par le client Flutter pour désigner une
-- catégorie sans dépendre du libellé accentué affiché à l'utilisateur.
--
-- Utilisation :
--   psql -U postgres -d codeci_db -f sql/migration_002_categorie_code.sql

ALTER TABLE categories_signalement
    ADD COLUMN IF NOT EXISTS code VARCHAR(50);

UPDATE categories_signalement SET code = 'depot_sauvage'     WHERE libelle = 'Dépôt sauvage';
UPDATE categories_signalement SET code = 'bac_plein'         WHERE libelle = 'Bac plein';
UPDATE categories_signalement SET code = 'bac_endommage'     WHERE libelle = 'Bac endommagé';
UPDATE categories_signalement SET code = 'dechet_dangereux'  WHERE libelle = 'Déchet dangereux';
UPDATE categories_signalement SET code = 'dechet_recyclable' WHERE libelle = 'Déchet recyclable';

ALTER TABLE categories_signalement
    ALTER COLUMN code SET NOT NULL,
    ADD CONSTRAINT categories_signalement_code_key UNIQUE (code);