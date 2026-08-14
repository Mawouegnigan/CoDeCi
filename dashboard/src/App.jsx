import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Signalements from './pages/Signalements';
import Tournees from './pages/Tournees';
import Carte from './pages/Carte';

const PROFILS_DASHBOARD = ['agent_municipal', 'entreprise', 'admin', 'ministere'];

function RouteProtegee({ children }) {
  const { utilisateur } = useAuth();
  const acces = utilisateur && PROFILS_DASHBOARD.includes(utilisateur.profil);
  return acces ? children : <Navigate to="/" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route
        path="/signalements"
        element={
          <RouteProtegee>
            <Signalements />
          </RouteProtegee>
        }
      />
      <Route
        path="/tournees"
        element={
          <RouteProtegee>
            <Tournees />
          </RouteProtegee>
        }
      />
      <Route
        path="/carte"
        element={
          <RouteProtegee>
            <Carte />
          </RouteProtegee>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}