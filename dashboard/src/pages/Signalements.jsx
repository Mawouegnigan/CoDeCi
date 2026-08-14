import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import { classeStatut } from '../utils/statut';

export default function Signalements() {
  const [signalements, setSignalements] = useState([]);
  const [total, setTotal] = useState(0);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');

  const { deconnexion } = useAuth();
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

  return (
    <Layout title="Signalements" subtitle={`${total} signalement${total > 1 ? 's' : ''}`}>
      {erreur && <div className="alert alert--error">{erreur}</div>}

      <div className="card">
        <div className="table-wrap">
          {chargement ? (
            <div className="loading-state">Chargement…</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Catégorie</th>
                  <th>Commune</th>
                  <th>Citoyen</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {signalements.length === 0 && (
                  <tr>
                    <td colSpan={5} className="td-muted">
                      Aucun signalement enregistré.
                    </td>
                  </tr>
                )}
                {signalements.map((s) => (
                  <tr key={s.id}>
                    <td className="mono">{new Date(s.date_creation).toLocaleDateString('fr-FR')}</td>
                    <td>{s.categorie.libelle}</td>
                    <td>{s.commune.nom}</td>
                    <td>{s.citoyen_nom}</td>
                    <td>
                      <span className={`badge ${classeStatut(s.statut)}`}>{s.statut}</span>
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