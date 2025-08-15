// src/pages/Home.jsx
import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";

export default function Home() {
  const navigate = useNavigate();

  const handleSearch = (lat, lon) => {
    navigate(`/realtime-parking?lat=${lat}&lon=${lon}`);
  };

  return (
    <div
      className="min-h-screen bg-cover bg-center flex flex-col items-center justify-center text-white relative"
      style={{ backgroundImage: "url('/background.jpg')" }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm" />

      {/* Content */}
      <div className="relative z-10 text-center px-4">
        <h1 className="text-5xl font-bold mb-4">FindMySpot 🚗</h1>
        <p className="text-xl mb-6">
          Find your nearest parking spot in Melbourne CBD
        </p>

        {/* SearchBar */}
        <div className="max-w-md mx-auto w-full">
          <SearchBar onSelect={handleSearch} />
        </div>

        {/* Action buttons */}
        <div className="mt-10 flex justify-center gap-4 flex-wrap">
          <button
            className="text-white px-5 py-2 rounded-lg font-medium hover:bg-white hover:text-black transition"
            onClick={() => navigate("/realtime-parking")}
          >
            Realtime Parking
          </button>
          <button
            className="text-white px-5 py-2 rounded-lg font-medium hover:bg-white hover:text-black transition"
            onClick={() => navigate("/parking-genie")}
          >
            Parking Genie
          </button>
          <button
            className="text-white px-5 py-2 rounded-lg font-medium hover:bg-white hover:text-black transition"
            onClick={() => navigate("/population-trends")}
          >
            Population Trends
          </button>
          <button
            className="text-white px-5 py-2 rounded-lg font-medium hover:bg-white hover:text-black transition"
            onClick={() => navigate("/vehicle-ownership")}
          >
            Vehicle Ownership
          </button>
        </div>
      </div>
    </div>
  );
}
