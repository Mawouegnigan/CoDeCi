import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import { classeStatut } from '../utils/statut';

function dateDuJour() {
  return new Date().toISOString().slice(0, 10);
}

export default function Tournees() {
  const [trajets, setTrajets] = useState([]);
  const [total, setTotal] = useState(0);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');
  const [dateFiltre, setDateFiltre] = useState(dateDuJour());
  const [optimisationEnCours, setOptimisationEnCours] = useState(null);
  const [messagesOptimisation, setMessagesOptimisation] = useState({});
  const { deconnexion } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    chargerTrajets(dateFiltre);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFiltre]);

  async function chargerTrajets(date) {
    setChargement(true);
    setErreur('');
    try {
      const reponse = await apiClient.get('/trajets', { params: { date_trajet: date } });
      setTrajets(reponse.data.items);
      setTotal(reponse.data.total);
    } catch (err) {
      if (err.response?.status === 401) {
        deconnexion();
        navigate('/');
      } else {
        setErreur('Impossible de charger les tournées.');
      }
    } finally {
      setChargement(false);
    }
  }

  async function optimiserTrajet(trajetId) {
    setOptimisationEnCours(trajetId);
    setMessagesOptimisation((precedent) => ({ ...precedent, [trajetId]: null }));

    try {
      await apiClient.post(`/trajets/${trajetId}/optimiser`);
      setMessagesOptimisation((precedent) => ({
        ...precedent,
        [trajetId]: { type: 'succes', texte: 'Ordre optimisé.' },
      }));
      await chargerTrajets(dateFiltre);
    } catch (err) {
      if (err.response?.status === 401) {
        deconnexion();
        navigate('/');
        return;
      }
      const detail = err.response?.data?.detail || "Échec de l'optimisation.";
      setMessagesOptimisation((precedent) => ({
        ...precedent,
        [trajetId]: { type: 'erreur', texte: detail },
      }));
    } finally {
      setOptimisationEnCours(null);
    }
  }

  return (
    <Layout title="Tournées" subtitle={`${total} tournée${total > 1 ? 's' : ''} · ${dateFiltre}`}>
      <div className="field">
        <label htmlFor="date-tournees">Date des tournées</label>
        <input
          id="date-tournees"
          type="date"
          value={dateFiltre}
          onChange={(e) => setDateFiltre(e.target.value)}
        />
      </div>

      {erreur && <div className="alert alert--error">{erreur}</div>}

      <div className="card">
        <div className="table-wrap">
          {chargement ? (
            <div className="loading-state">Chargement…</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Camion</th>
                  <th>Entreprise</th>
                  <th>Chauffeur</th>
                  <th>Statut</th>
                  <th>Bacs collectés</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {trajets.length === 0 && (
                  <tr>
                    <td colSpan={6} className="td-muted">
                      Aucune tournée pour cette date.
                    </td>
                  </tr>
                )}
                {trajets.map((t) => (
                  <tr key={t.id}>
                    <td className="mono">{t.camion_matricule}</td>
                    <td>{t.entreprise_nom}</td>
                    <td>{t.chauffeur_nom}</td>
                    <td>
                      <span className={`badge ${classeStatut(t.statut)}`}>{t.statut}</span>
                    </td>
                    <td className="mono">
                      {t.nombre_bacs_collectes} / {t.nombre_bacs_total}
                    </td>
                    <td>
                      <button
                        className="btn btn--primary"
                        onClick={() => optimiserTrajet(t.id)}
                        disabled={t.statut === 'termine' || optimisationEnCours === t.id}
                      >
                        {optimisationEnCours === t.id ? 'Optimisation…' : 'Optimiser'}
                      </button>
                      {messagesOptimisation[t.id] && (
                        <div
                          className={
                            messagesOptimisation[t.id].type === 'erreur'
                              ? 'inline-message inline-message--erreur'
                              : 'inline-message inline-message--succes'
                          }
                        >
                          {messagesOptimisation[t.id].texte}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
}