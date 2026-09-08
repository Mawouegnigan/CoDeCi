-- Ajoute une valeur d'enum dédiée au recrédit de points en cas
-- d'échec confirmé d'un paiement MoMo. Sans cette distinction, le
-- ledger ne pourrait pas différencier un débit d'un recrédit, ce qui
-- casserait l'auditabilité du système de points.

ALTER TYPE type_transaction_points ADD VALUE 'annulation_conversion';