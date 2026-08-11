import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Map, { Marker, Popup } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const COULEUR_STATUT_BAC = {
  vide: '#4caf50',
  moyen: '#ff9800',
  plein: '#f44336',
};

export default function Carte() {
  const [bacs, setBacs] = useState([]);
  const [signalements, setSignalements] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');
  const [selection, setSelection] = useState(null);

  const { utilisateur, deconnexion } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    async function chargerDonnees() {
      try {
        const [reponseBacs, reponseSignalements] = await Promise.all([
          apiClient.get('/bacs'),
          apiClient.get('/signalements'),
        ]);
        setBacs(reponseBacs.data.items);
        setSignalements(reponseSignalements.data.items);
      } catch (err) {
        if (err.response?.status === 401) {
          deconnexion();
          navigate('/');
        } else {
          setErreur('Impossible de charger les données de la carte.');
        }
      } finally {
        setChargement(false);
      }
    }

    chargerDonnees();
  }, [deconnexion, navigate]);

  function gererDeconnexion() {
    deconnexion();
    navigate('/');
  }

  if (chargement) return <p style={{ padding: '24px' }}>Chargement...</p>;

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Carte ({bacs.length} bacs, {signalements.length} signalements)</h1>
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

      <div style={{ height: '600px', marginTop: '16px' }}>
        <Map
          mapboxAccessToken={MAPBOX_TOKEN}
          initialViewState={{ longitude: -4.008, latitude: 5.36, zoom: 12 }}
          style={{ width: '100%', height: '100%' }}
          mapStyle="mapbox://styles/mapbox/streets-v12"
        >
          {bacs.map((bac) => (
            <Marker
              key={`bac-${bac.id}`}
              longitude={bac.longitude}
              latitude={bac.latitude}
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelection({ type: 'bac', data: bac });
              }}
            >
              <div
                title={`Bac - ${bac.statut}`}
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  backgroundColor: COULEUR_STATUT_BAC[bac.statut] || '#999',
                  border: '2px solid white',
                  cursor: 'pointer',
                }}
              />
            </Marker>
          ))}

          {signalements.map((s) => (
            <Marker
              key={`signalement-${s.id}`}
              longitude={s.longitude}
              latitude={s.latitude}
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelection({ type: 'signalement', data: s });
              }}
            >
              <div
                title={`Signalement - ${s.categorie.libelle}`}
                style={{
                  width: '0',
                  height: '0',
                  borderLeft: '8px solid transparent',
                  borderRight: '8px solid transparent',
                  borderBottom: '16px solid #2196f3',
                  cursor: 'pointer',
                }}
              />
            </Marker>
          ))}

          {selection && (
            <Popup
              longitude={selection.data.longitude}
              latitude={selection.data.latitude}
              onClose={() => setSelection(null)}
              closeOnClick={false}
            >
              {selection.type === 'bac' ? (
                <div>
                  <strong>Bac public</strong>
                  <p>Statut : {selection.data.statut}</p>
                  <p>Commune : {selection.data.commune_nom}</p>
                </div>
              ) : (
                <div>
                  <strong>Signalement</strong>
                  <p>{selection.data.categorie.libelle}</p>
                  <p>Commune : {selection.data.commune.nom}</p>
                  <p>Statut : {selection.data.statut}</p>
                </div>
              )}
            </Popup>
          )}
        </Map>
      </div>
    </div>
  );
}