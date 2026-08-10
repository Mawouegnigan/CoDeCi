import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [telephone, setTelephone] = useState('');
  const [motDePasse, setMotDePasse] = useState('');
  const [erreur, setErreur] = useState('');
  const [chargement, setChargement] = useState(false);

  const { connexion } = useAuth();
  const navigate = useNavigate();

  async function gererSoumission(e) {
    e.preventDefault();
    setErreur('');
    setChargement(true);

    try {
      await connexion(telephone, motDePasse);
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
    <div style={{ maxWidth: '360px', margin: '80px auto', fontFamily: 'sans-serif' }}>
      <h1>CoDeCI — Dashboard</h1>
      <form onSubmit={gererSoumission}>
        <div style={{ marginBottom: '12px' }}>
          <label>Téléphone</label>
          <input
            type="text"
            value={telephone}
            onChange={(e) => setTelephone(e.target.value)}
            style={{ width: '100%', padding: '8px' }}
            required
          />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label>Mot de passe</label>
          <input
            type="password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            style={{ width: '100%', padding: '8px' }}
            required
          />
        </div>
        {erreur && <p style={{ color: 'red' }}>{erreur}</p>}
        <button type="submit" disabled={chargement} style={{ padding: '8px 16px' }}>
          {chargement ? 'Connexion...' : 'Se connecter'}
        </button>
      </form>
    </div>
  );
}