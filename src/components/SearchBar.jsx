// src/components/SearchBar.jsx
import { useState } from "react";
import axios from "axios";

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [selectedCoords, setSelectedCoords] = useState(null); // store selected coords

  const handleChange = async (e) => {
    const q = e.target.value;
    setQuery(q);
    setSelectedCoords(null); // reset previous selection
    if (q.length > 3) {
      try {
        const res = await axios.get(`/api/parking/autocomplete?q=${q}`);
        setSuggestions(res.data || []);
      } catch (error) {
        console.error("Autocomplete error:", error);
      }
    } else {
      setSuggestions([]);
    }
  };

  const handleSelect = (suggestion) => {
    setQuery(suggestion.display_name);
    setSuggestions([]);
    setSelectedCoords({ lat: suggestion.lat, lon: suggestion.lon });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedCoords && onSelect) {
      onSelect(selectedCoords.lat, selectedCoords.lon);
    } else {
      alert("Please select a location from the list.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex gap-2">
      <input
        value={query}
        onChange={handleChange}
        placeholder="Enter an address in Melbourne CBD"
        className="w-full px-4 py-2 text-black rounded-md border focus:outline-none focus:ring-2 focus:ring-white"
      />
      <button
        type="submit"
        className="bg-white text-black px-4 py-2 rounded-md font-medium hover:bg-gray-200 transition"
      >
        Search
      </button>
      {suggestions.length > 0 && (
        <ul className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-md shadow max-h-60 overflow-auto z-50 text-black text-left">
          {suggestions.map((s, idx) => (
            <li
              key={idx}
              onClick={() => handleSelect(s)}
              className="px-4 py-2 hover:bg-gray-200 cursor-pointer"
            >
              {s.display_name}
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
