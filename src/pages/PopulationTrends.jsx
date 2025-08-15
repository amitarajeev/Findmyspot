import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ChartWrapper from '../components/ChartWrapper';

const PopulationTrends = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get('/api/trends/population')
      .then(res => setData(res.data.trends || []))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">👥 Population Growth Trends</h1>
        <ChartWrapper title="CBD Population Growth Over Years" data={data} />
      </div>
    </div>
  );
};

export default PopulationTrends;
