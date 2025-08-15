// src/components/ChartWrapper.jsx
import React from 'react';

const ChartWrapper = ({ title, data }) => {
  return (
    <div className="bg-white p-6 shadow rounded">
      <h2 className="text-lg font-semibold mb-4">{title}</h2>
      {data.length === 0 ? (
        <p className="text-gray-500">No data to display.</p>
      ) : (
        <div>
          {/* Replace this with Chart.js / ECharts later */}
          <pre className="text-sm bg-gray-100 p-3 rounded overflow-x-auto">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ChartWrapper;
