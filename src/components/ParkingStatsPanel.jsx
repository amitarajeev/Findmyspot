// src/components/ParkingStatsPanel.jsx
import React from "react";

const ParkingStatsPanel = ({ data, userCoords }) => {
  const haversine = (lat1, lon1, lat2, lon2) => {
    const R = 6371e3;
    const toRad = deg => (deg * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  return (
    <div className="space-y-4 text-white">
      <h2 className="text-xl font-bold text-black">📊 Real-Time Stats</h2>
      {data?.map((zone, idx) => (
        <div
          key={idx}
          className="bg-gray-800 p-4 rounded shadow border border-gray-600"
        >
          <p className="font-semibold text-white">Zone: {zone.zone}</p>
          <p>🟢 Available: {zone.available}</p>
          <p>🔴 Occupied: {zone.occupied}</p>
          <hr className="my-2 border-gray-600" />
          <p className="font-semibold text-white">Nearest Bays:</p>
          <ul className="text-sm text-gray-200">
            {zone.nearestBays.map((bay, i) => {
              const distance = userCoords
                ? haversine(userCoords.lat, userCoords.lon, bay.lat, bay.lon)
                : 0;
              return (
                <li key={i} className="my-2">
                  • {bay.status} – {Math.round(distance)}m away
                  <br />
                  <a
                    href={`https://www.google.com/maps?q=${bay.lat},${bay.lon}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-300 underline"
                  >
                    Open in Google Maps
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default ParkingStatsPanel;
