import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Signalements() {
  const [signalements, setSignalements] = useState([]);
  const [total, setTotal] = useState(0);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');

  const { utilisateur, deconnexion } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    async function chargerSignalements() {
      try {
        const reponse = await apiClient.get('/signalements');
        setSignalements(reponse.data.items);
        setTotal(reponse.data.total);
      } catch (err) {
        if (err.response?.status === 401) {
          deconnexion();
          navigate('/');
        } else {
          setErreur('Impossible de charger les signalements.');
        }
      } finally {
        setChargement(false);
      }
    }

    chargerSignalements();
  }, [deconnexion, navigate]);

  function gererDeconnexion() {
    deconnexion();
    navigate('/');
  }

  if (chargement) return <p style={{ padding: '24px' }}>Chargement...</p>;

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Signalements ({total})</h1>
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
      
      {erreur && <p style={{ color: 'red' }}>{erreur}</p>}

      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #ccc' }}>
            <th style={{ padding: '8px' }}>Date</th>
            <th style={{ padding: '8px' }}>Catégorie</th>
            <th style={{ padding: '8px' }}>Commune</th>
            <th style={{ padding: '8px' }}>Citoyen</th>
            <th style={{ padding: '8px' }}>Statut</th>
          </tr>
        </thead>
        <tbody>
          {signalements.map((s) => (
            <tr key={s.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '8px' }}>{new Date(s.date_creation).toLocaleDateString('fr-FR')}</td>
              <td style={{ padding: '8px' }}>{s.categorie.libelle}</td>
              <td style={{ padding: '8px' }}>{s.commune.nom}</td>
              <td style={{ padding: '8px' }}>{s.citoyen_nom}</td>
              <td style={{ padding: '8px' }}>{s.statut}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}