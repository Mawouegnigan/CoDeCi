import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Signalements from './pages/Signalements';
import Tournees from './pages/Tournees';

function RouteProtegee({ children }) {
  const { utilisateur } = useAuth();
  return utilisateur ? children : <Navigate to="/" replace />;
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