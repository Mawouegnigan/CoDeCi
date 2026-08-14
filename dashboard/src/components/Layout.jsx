import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LIENS = [
  { to: '/signalements', label: 'Signalements' },
  { to: '/tournees', label: 'Tournées' },
  { to: '/carte', label: 'Carte' },
];

export default function Layout({ title, subtitle, children }) {
  const { utilisateur, deconnexion } = useAuth();
  const navigate = useNavigate();

  function gererDeconnexion() {
    deconnexion();
    navigate('/');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <span className="sidebar__stamp">CDC</span>
          <div>
            <div className="sidebar__title">CoDeCI</div>
            <div className="sidebar__subtitle">Collecte de Déchets</div>
          </div>
        </div>

        <nav className="sidebar__nav">
          {LIENS.map((lien) => (
            <NavLink
              key={lien.to}
              to={lien.to}
              className={({ isActive }) =>
                'sidebar__link' + (isActive ? ' sidebar__link--active' : '')
              }
            >
              {lien.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__user">
          <div className="sidebar__user-name">{utilisateur?.nom}</div>
          <div className="sidebar__user-role">{utilisateur?.profil}</div>
          <button className="btn btn--ghost" onClick={gererDeconnexion}>
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="main__header">
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </header>
        <div className="main__content">{children}</div>
      </main>
    </div>
  );
}