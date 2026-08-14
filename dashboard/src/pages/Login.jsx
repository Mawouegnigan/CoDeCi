import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PROFILS_DASHBOARD = ['agent_municipal', 'entreprise', 'admin', 'ministere'];

export default function Login() {
  const [telephone, setTelephone] = useState('');
  const [motDePasse, setMotDePasse] = useState('');
  const [erreur, setErreur] = useState('');
  const [chargement, setChargement] = useState(false);

  const { connexion, deconnexion } = useAuth();
  const navigate = useNavigate();

  async function gererSoumission(e) {
    e.preventDefault();
    setErreur('');
    setChargement(true);

    try {
      const utilisateurConnecte = await connexion(telephone, motDePasse);

      if (!PROFILS_DASHBOARD.includes(utilisateurConnecte.profil)) {
        deconnexion();
        setErreur(
          "Ce compte n'a pas accès au dashboard web. L'application mobile CoDeCI est réservée aux chauffeurs et citoyens."
        );
        return;
      }

      navigate('/signalements');
    } catch (err) {
      if (err.response?.status === 401) {
        setErreur('Téléphone ou mot de passe incorrect.');
      } else {
        setErreur('Erreur de connexion au serveur. Vérifiez que le backend est démarré.');
      }
    } finally {
      setChargement(false);
    }
  }

  return (
    <div style={{ maxWidth: '360px', margin: '80px auto', fontFamily: 'var(--font-body)' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '24px' }}>CoDeCI — Dashboard</h1>
      <form onSubmit={gererSoumission} className="card" style={{ padding: '24px' }}>
        <div className="field" style={{ maxWidth: 'none' }}>
          <label htmlFor="telephone">Téléphone</label>
          <input
            id="telephone"
            type="text"
            value={telephone}
            onChange={(e) => setTelephone(e.target.value)}
            required
          />
        </div>
        <div className="field" style={{ maxWidth: 'none' }}>
          <label htmlFor="mot-de-passe">Mot de passe</label>
          <input
            id="mot-de-passe"
            type="password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            required
          />
        </div>
        {erreur && <div className="alert alert--error">{erreur}</div>}
        <button type="submit" disabled={chargement} className="btn btn--primary" style={{ width: '100%' }}>
          {chargement ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
    </div>
  );
}