// src/components/MapView.jsx
import React from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const blueIcon = new L.Icon({
  iconUrl: "https://maps.gstatic.com/mapfiles/ms2/micons/blue-dot.png",
  iconSize: [32, 32],
});

const greenIcon = new L.Icon({
  iconUrl: "https://maps.gstatic.com/mapfiles/ms2/micons/green-dot.png",
  iconSize: [32, 32],
});

const redIcon = new L.Icon({
  iconUrl: "https://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png",
  iconSize: [32, 32],
});

const MapView = ({ center, bluePin, greenPins, redPins }) => {
  if (!center) return <p className="text-center mt-10">Loading map...</p>;

  return (
    <MapContainer
      center={[center.lat, center.lon]}
      zoom={17}
      style={{ height: "100vh", width: "100%" }}
      scrollWheelZoom
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {bluePin && (
        <Marker position={[bluePin.lat, bluePin.lon]} icon={blueIcon}>
          <Popup>Searched Location</Popup>
        </Marker>
      )}

      {greenPins.map((spot, idx) => (
        <Marker
          key={`green-${idx}`}
          position={[spot.lat, spot.lon]}
          icon={greenIcon}
          eventHandlers={{
            click: () => {
              const url = `https://www.google.com/maps/dir/?api=1&destination=${spot.lat},${spot.lon}`;
              window.open(url, "_blank");
            },
          }}
        >
          <Popup>🟢 Unoccupied Spot (Zone {spot.zone})</Popup>
        </Marker>
      ))}

      {redPins.map((spot, idx) => (
        <Marker
          key={`red-${idx}`}
          position={[spot.lat, spot.lon]}
          icon={redIcon}
          eventHandlers={{
            click: () => {
              const url = `https://www.google.com/maps/dir/?api=1&destination=${spot.lat},${spot.lon}`;
              window.open(url, "_blank");
            },
          }}
        >
          <Popup>🔴 Occupied Spot (Zone {spot.zone})</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default MapView;
