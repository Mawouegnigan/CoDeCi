import { createContext, useContext, useState } from 'react';
import apiClient from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(() => {
    const stored = localStorage.getItem('codeci_utilisateur');
    return stored ? JSON.parse(stored) : null;
  });

  async function connexion(telephone, motDePasse) {
    const reponse = await apiClient.post('/auth/connexion', {
      telephone,
      mot_de_passe: motDePasse,
    });

    const { access_token, utilisateur: utilisateurConnecte } = reponse.data;

    localStorage.setItem('codeci_token', access_token);
    localStorage.setItem('codeci_utilisateur', JSON.stringify(utilisateurConnecte));
    setUtilisateur(utilisateurConnecte);

    return utilisateurConnecte;
  }

  function deconnexion() {
    localStorage.removeItem('codeci_token');
    localStorage.removeItem('codeci_utilisateur');
    setUtilisateur(null);
  }

  return (
    <AuthContext.Provider value={{ utilisateur, connexion, deconnexion }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth doit être utilisé à l’intérieur d’un AuthProvider');
  }
  return context;
}