// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import RealtimeParking from "./pages/RealtimeParking";
import ParkingGenie from "./pages/ParkingGenie";
import PopulationTrends from "./pages/PopulationTrends";
import VehicleOwnership from "./pages/VehicleOwnership";
import Navbar from "./components/Navbar";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/realtime-parking" element={<RealtimeParking />} />
        <Route path="/parking-genie" element={<ParkingGenie />} />
        <Route path="/population-trends" element={<PopulationTrends />} />
        <Route path="/vehicle-ownership" element={<VehicleOwnership />} />
      </Routes>
    </Router>
  );
}

export default App;
