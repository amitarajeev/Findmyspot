import React, { useState } from 'react';
import axios from 'axios';

const ParkingGenie = () => {
  const [day, setDay] = useState('Monday');
  const [hour, setHour] = useState('09');
  const [zone, setZone] = useState('7539'); // Default test zone
  const [duration, setDuration] = useState(1);
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState('');

  const fetchPredictions = async () => {
    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const res = await axios.get(
        `/api/parking/predict_many?zone_number=${zone}&hour=${hour}&day_type=${day}&hours_ahead=${duration}`
      );
      const data = res.data?.items || [];

      if (data.length === 0) {
        setError('❗ No predictions returned for the selected time.');
      } else {
        setRecommendations(data);
      }
    } catch (err) {
      console.error(err);
      setError('❗ Failed to fetch predictions. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-4xl mx-auto bg-gray-900 p-6 rounded shadow">
        <h1 className="text-3xl font-bold mb-6 text-center">🧞 Parking Genie</h1>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm mb-1">Zone Number</label>
            <input
              type="number"
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              className="w-full p-2 rounded text-black"
              placeholder="e.g., 7539"
            />
          </div>

          <div>
            <label className="block text-sm mb-1">Day of Week</label>
            <select
              value={day}
              onChange={(e) => setDay(e.target.value)}
              className="w-full p-2 rounded text-black"
            >
              {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm mb-1">Start Hour</label>
            <input
              type="number"
              min={0}
              max={23}
              value={hour}
              onChange={(e) => setHour(e.target.value)}
              className="w-full p-2 rounded text-black"
              placeholder="14 for 2 PM"
            />
          </div>

          <div>
            <label className="block text-sm mb-1">Duration (hrs)</label>
            <input
              type="number"
              min={1}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full p-2 rounded text-black"
            />
          </div>
        </div>

        <button
          onClick={fetchPredictions}
          className="bg-white text-black px-6 py-2 rounded font-semibold hover:bg-gray-200 transition"
        >
          🔮 Predict Best Parking
        </button>

        <div className="mt-6">
          {loading && <p className="text-blue-300">⏳ Fetching predictions...</p>}
          {error && <p className="text-red-400 mt-2">{error}</p>}

          {recommendations.length > 0 && (
            <ul className="mt-4 space-y-4">
              {recommendations.map((rec, idx) => (
                <li key={idx} className="p-4 rounded border border-gray-700 bg-gray-800">
                  <p><strong>📍 Location:</strong> {rec.location}</p>
                  <p><strong>🕒 Time:</strong> {rec.hour}:00 on {rec.day_type}</p>
                  <p><strong>🚗 Available Spots:</strong> {rec.available_spots}</p>
                  <p><strong>Status:</strong> <span className="font-semibold">{rec.status}</span></p>
                  <p><strong>Confidence:</strong> {rec.confidence_score}</p>
                  <a
                    href={`https://www.google.com/maps?q=${rec.lat},${rec.lon}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 underline mt-2 inline-block"
                  >
                    Open in Google Maps
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default ParkingGenie;
