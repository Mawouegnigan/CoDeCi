import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

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
  const { utilisateur, deconnexion } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    chargerTrajets(dateFiltre);
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
      const detail = err.response?.data?.detail || 'Échec de l\'optimisation.';
      setMessagesOptimisation((precedent) => ({
        ...precedent,
        [trajetId]: { type: 'erreur', texte: detail },
      }));
    } finally {
      setOptimisationEnCours(null);
    }
  }

  function gererDeconnexion() {
    deconnexion();
    navigate('/');
  }

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Tournées ({total})</h1>
        <div>
          <span style={{ marginRight: '12px' }}>{utilisateur?.nom} ({utilisateur?.profil})</span>
          <button onClick={gererDeconnexion}>Déconnexion</button>
        </div>
      </div>
      <nav style={{ margin: '16px 0' }}>
        <a href="/signalements" style={{ marginRight: '16px' }}>Signalements</a>
        <a href="/tournees" style={{ marginRight: '16px' }}>Tournées</a>
        <a href="/carte">Carte</a>
      </nav>

      <div style={{ margin: '16px 0' }}>
        <label>
          Date des tournées :{' '}
          <input
            type="date"
            value={dateFiltre}
            onChange={(e) => setDateFiltre(e.target.value)}
          />
        </label>
      </div>

      {erreur && <p style={{ color: 'red' }}>{erreur}</p>}
      {chargement ? (
        <p>Chargement...</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '2px solid #ccc' }}>
              <th style={{ padding: '8px' }}>Camion</th>
              <th style={{ padding: '8px' }}>Entreprise</th>
              <th style={{ padding: '8px' }}>Chauffeur</th>
              <th style={{ padding: '8px' }}>Statut</th>
              <th style={{ padding: '8px' }}>Bacs collectés</th>
              <th style={{ padding: '8px' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {trajets.length === 0 && (
              <tr>
                <td colSpan={6} style={{ padding: '8px', color: '#888' }}>
                  Aucune tournée pour cette date.
                </td>
              </tr>
            )}
            {trajets.map((t) => (
              <tr key={t.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '8px' }}>{t.camion_matricule}</td>
                <td style={{ padding: '8px' }}>{t.entreprise_nom}</td>
                <td style={{ padding: '8px' }}>{t.chauffeur_nom}</td>
                <td style={{ padding: '8px' }}>{t.statut}</td>
                <td style={{ padding: '8px' }}>{t.nombre_bacs_collectes} / {t.nombre_bacs_total}</td>
                <td style={{ padding: '8px' }}>
                  <button
                    onClick={() => optimiserTrajet(t.id)}
                    disabled={t.statut === 'termine' || optimisationEnCours === t.id}
                  >
                    {optimisationEnCours === t.id ? 'Optimisation...' : 'Optimiser'}
                  </button>
                  {messagesOptimisation[t.id] && (
                    <div
                      style={{
                        fontSize: '12px',
                        marginTop: '4px',
                        color: messagesOptimisation[t.id].type === 'erreur' ? 'red' : 'green',
                      }}
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
  );
}