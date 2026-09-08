-- Alignement de transactions_points sur l'architecture ledger complète.
-- La table et les types existaient déjà partiellement en base (posés
-- lors d'une session précédente) ; ce script complète sans recréer.

-- Renommage pour cohérence avec le code (montant_points, plus explicite
-- que "points" une fois qu'on distingue montant_points de montant_fcfa).
ALTER TABLE transactions_points RENAME COLUMN points TO montant_points;

-- Colonnes manquantes
ALTER TABLE transactions_points ADD COLUMN statut statut_transaction_points NOT NULL DEFAULT 'reussi';
ALTER TABLE transactions_points ADD COLUMN montant_fcfa INTEGER;
ALTER TABLE transactions_points ADD COLUMN numero_telephone VARCHAR(20);
ALTER TABLE transactions_points ADD COLUMN reference_externe VARCHAR(100);
ALTER TABLE transactions_points ADD COLUMN date_maj TIMESTAMPTZ DEFAULT now();

-- Idempotence : garantit qu'un signalement ne peut jamais être crédité
-- deux fois. Vérifié juste avant qu'aucun doublon n'existe déjà.
ALTER TABLE transactions_points ADD CONSTRAINT transactions_points_signalement_id_key UNIQUE (signalement_id);

-- Suppression de l'index redondant (idx_transactions_utilisateur fait
-- doublon exact avec idx_transactions_points_utilisateur).
DROP INDEX IF EXISTS idx_transactions_utilisateur;