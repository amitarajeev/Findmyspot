import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-white bg-opacity-70 backdrop-blur sticky top-0 z-50 shadow-sm w-full">
      <div className="flex justify-between items-center px-8 py-3">
        
        {/* Left-aligned logo */}
        <div className="text-left">
          <Link to="/" className="text-2xl font-bold text-black">
            FindMySpot
          </Link>
        </div>

        {/* Right-aligned nav links */}
        <div className="flex gap-8 text-sm font-medium text-gray-800">
          <Link to="/realtime-parking" className="hover:underline">
            Realtime Parking
          </Link>
          <Link to="/parking-genie" className="hover:underline">
            Parking Genie
          </Link>
          <Link to="/population-trends" className="hover:underline">
            Population
          </Link>
          <Link to="/vehicle-ownership" className="hover:underline">
            Vehicles
          </Link>
        </div>
      </div>
    </nav>
  );
}
