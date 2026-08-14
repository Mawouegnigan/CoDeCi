import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Map, { Marker, Popup } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const COULEUR_STATUT_BAC = {
  vide: '#3F7355',
  moyen: '#C97A2B',
  plein: '#A83232',
};

export default function Carte() {
  const [bacs, setBacs] = useState([]);
  const [signalements, setSignalements] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');
  const [selection, setSelection] = useState(null);

  const { deconnexion } = useAuth();
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

  return (
    <Layout title="Carte" subtitle={`${bacs.length} bacs · ${signalements.length} signalements`}>
      {erreur && <div className="alert alert--error">{erreur}</div>}

      {chargement ? (
        <div className="loading-state">Chargement…</div>
      ) : (
        <div className="map-card">
          <Map
            mapboxAccessToken={MAPBOX_TOKEN}
            initialViewState={{ longitude: -4.008, latitude: 5.36, zoom: 12 }}
            style={{ width: '100%', height: '100%' }}
            mapStyle="mapbox://styles/mapbox/light-v11"
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
                  className="map-marker--bac"
                  style={{ backgroundColor: COULEUR_STATUT_BAC[bac.statut] || '#8A8F8D' }}
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
                <div title={`Signalement - ${s.categorie.libelle}`} className="map-marker--signalement" />
              </Marker>
            ))}

            {selection && (
              <Popup
                longitude={selection.data.longitude}
                latitude={selection.data.latitude}
                onClose={() => setSelection(null)}
                closeOnClick={false}
              >
                <div className="map-popup">
                  {selection.type === 'bac' ? (
                    <>
                      <strong>Bac public</strong>
                      <p>Statut : {selection.data.statut}</p>
                      <p>Commune : {selection.data.commune_nom}</p>
                    </>
                  ) : (
                    <>
                      <strong>Signalement</strong>
                      <p>{selection.data.categorie.libelle}</p>
                      <p>Commune : {selection.data.commune.nom}</p>
                      <p>Statut : {selection.data.statut}</p>
                    </>
                  )}
                </div>
              </Popup>
            )}
          </Map>
        </div>
      )}
    </Layout>
  );
}