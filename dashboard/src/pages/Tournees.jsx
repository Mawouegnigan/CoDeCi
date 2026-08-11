import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Tournees() {
  const [trajets, setTrajets] = useState([]);
  const [total, setTotal] = useState(0);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');

  const { utilisateur, deconnexion } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    async function chargerTrajets() {
      try {
        const reponse = await apiClient.get('/trajets');
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

    chargerTrajets();
  }, [deconnexion, navigate]);

  function gererDeconnexion() {
    deconnexion();
    navigate('/');
  }

  if (chargement) return <p style={{ padding: '24px' }}>Chargement...</p>;

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Tournées du jour ({total})</h1>
        <div>
          <span style={{ marginRight: '12px' }}>{utilisateur?.nom} ({utilisateur?.profil})</span>
          <button onClick={gererDeconnexion}>Déconnexion</button>
        </div>
      </div>

      <nav style={{ margin: '16px 0' }}>
        <a href="/signalements" style={{ marginRight: '16px' }}>Signalements</a>
        <a href="/tournees">Tournées</a>
      </nav>

      {erreur && <p style={{ color: 'red' }}>{erreur}</p>}

      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #ccc' }}>
            <th style={{ padding: '8px' }}>Camion</th>
            <th style={{ padding: '8px' }}>Entreprise</th>
            <th style={{ padding: '8px' }}>Chauffeur</th>
            <th style={{ padding: '8px' }}>Statut</th>
            <th style={{ padding: '8px' }}>Bacs collectés</th>
          </tr>
        </thead>
        <tbody>
          {trajets.map((t) => (
            <tr key={t.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '8px' }}>{t.camion_matricule}</td>
              <td style={{ padding: '8px' }}>{t.entreprise_nom}</td>
              <td style={{ padding: '8px' }}>{t.chauffeur_nom}</td>
              <td style={{ padding: '8px' }}>{t.statut}</td>
              <td style={{ padding: '8px' }}>{t.nombre_bacs_collectes} / {t.nombre_bacs_total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}