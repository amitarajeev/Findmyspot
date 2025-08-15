// src/pages/RealtimeParking.jsx
import React, { useEffect, useState } from "react";
import MapView from "../components/MapView";
import ParkingStatsPanel from "../components/ParkingStatsPanel";
import axios from "axios";

const ZONES = [7539, 7814, 7550]; // Can be updated dynamically if needed

const RealtimeParking = () => {
  const [greenPins, setGreenPins] = useState([]);
  const [redPins, setRedPins] = useState([]);
  const [stats, setStats] = useState([]);
  const [center, setCenter] = useState({ lat: -37.814, lon: 144.963 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const allGreen = [];
      const allRed = [];
      const statsList = [];

      try {
        for (const zone of ZONES) {
          const res = await axios.get(`/api/parking/realtime?zone_number=${zone}`);
          const items = res.data?.items || [];

          const green = items
            .filter(i => i.status === "Unoccupied")
            .map(i => ({ ...i, zone }));

          const red = items
            .filter(i => i.status !== "Unoccupied")
            .map(i => ({ ...i, zone }));

          allGreen.push(...green);
          allRed.push(...red);

          statsList.push({
            zone,
            available: green.length,
            occupied: red.length,
            nearestBays: [...green, ...red].slice(0, 5)
          });

          if (!center && green.length > 0) {
            setCenter({ lat: green[0].lat, lon: green[0].lon });
          }
        }

        setGreenPins(allGreen);
        setRedPins(allRed);
        setStats(statsList);
      } catch (err) {
        console.error("Error fetching realtime data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="flex flex-col md:flex-row h-screen w-full">
      <div className="w-full md:w-3/5 h-1/2 md:h-full">
        {loading ? (
          <div className="flex justify-center items-center h-full">
            <p className="text-gray-500 text-lg">Loading map...</p>
          </div>
        ) : (
          <MapView
            center={center}
            bluePin={center}
            greenPins={greenPins}
            redPins={redPins}
          />
        )}
      </div>
      <div className="w-full md:w-2/5 h-1/2 md:h-full overflow-y-auto bg-gray-100 p-4">
        <ParkingStatsPanel data={stats} userCoords={center} />
      </div>
    </div>
  );
};

export default RealtimeParking;
