const STYLES_STATUT = {
  vide: 'badge--vide',
  moyen: 'badge--moyen',
  plein: 'badge--plein',
  planifie: 'badge--planifie',
  en_cours: 'badge--moyen',
  termine: 'badge--vide',
  en_attente: 'badge--moyen',
};

export function classeStatut(statut) {
  const normalise = (statut || '').toLowerCase();
  return STYLES_STATUT[normalise] || 'badge--defaut';
}