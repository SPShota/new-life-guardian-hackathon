import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// アイコンの設定
const bearIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const homeIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const familyIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// 新居の位置（長野市）
const HOME_POSITION = [36.6513, 138.1810];

function MapUpdater({ selectedSighting }) {
  const map = useMap();
  
  useEffect(() => {
    if (selectedSighting) {
      map.setView([selectedSighting.latitude, selectedSighting.longitude], 15);
    }
  }, [selectedSighting, map]);
  
  return null;
}

function MapView({ bearSightings, familyMembers, selectedSighting, onSelectSighting }) {
  const mapRef = useRef(null);

  return (
    <MapContainer
      center={HOME_POSITION}
      zoom={13}
      style={{ height: '100%', width: '100%' }}
      ref={mapRef}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <MapUpdater selectedSighting={selectedSighting} />
      
      {/* 新居の位置 */}
      <Marker position={HOME_POSITION} icon={homeIcon}>
        <Popup>
          <strong>🏠 新居</strong>
        </Popup>
      </Marker>
      
      {/* 熊出没情報 */}
      {bearSightings.map((sighting) => (
        <React.Fragment key={sighting.id}>
          <Marker
            position={[sighting.latitude, sighting.longitude]}
            icon={bearIcon}
            eventHandlers={{
              click: () => onSelectSighting(sighting)
            }}
          >
            <Popup>
              <div>
                <strong>🐻 熊出没情報</strong>
                <p><strong>日付:</strong> {sighting.date}</p>
                <p><strong>場所:</strong> {sighting.location}</p>
                <p><strong>詳細:</strong> {sighting.description}</p>
                {sighting.distance_from_home && (
                  <p><strong>新居からの距離:</strong> {sighting.distance_from_home}km</p>
                )}
              </div>
            </Popup>
          </Marker>
          {/* 危険エリア（500m半径） */}
          <Circle
            center={[sighting.latitude, sighting.longitude]}
            radius={500}
            pathOptions={{
              color: '#ff0000',
              fillColor: '#ff0000',
              fillOpacity: 0.2
            }}
          />
        </React.Fragment>
      ))}
      
      {/* 家族の位置 */}
      {familyMembers.map((member) => (
        <Marker
          key={member.id}
          position={[member.latitude, member.longitude]}
          icon={familyIcon}
        >
          <Popup>
            <div>
              <strong>👤 {member.name}</strong>
              <p><strong>更新時刻:</strong> {new Date(member.timestamp).toLocaleString('ja-JP')}</p>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default MapView;
