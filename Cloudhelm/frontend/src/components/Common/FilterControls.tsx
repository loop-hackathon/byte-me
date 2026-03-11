import React from 'react';

interface FilterControlsProps {
  timeRange: string;
  environment: string;
  onTimeRangeChange: (range: string) => void;
  onEnvironmentChange: (env: string) => void;
}

export default function FilterControls({ 
  timeRange, 
  environment, 
  onTimeRangeChange, 
  onEnvironmentChange 
}: FilterControlsProps) {
  return (
    <>
      {/* Environment Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-slate-400">Environment:</label>
        <select
          value={environment}
          onChange={(e) => onEnvironmentChange(e.target.value)}
          className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-slate-100"
        >
          <option value="all">All</option>
          <option value="prod">Production</option>
          <option value="staging">Staging</option>
          <option value="dev">Development</option>
        </select>
      </div>
      
      {/* Time Range Filter */}
      <div className="flex items-center gap-2 bg-slate-900/60 backdrop-blur-lg rounded-lg p-1 border border-slate-700">
        {['7d', '30d', '90d'].map((range) => (
          <button
            key={range}
            onClick={() => onTimeRangeChange(range)}
            className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-all ${
              timeRange === range
                ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-slate-100 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                : 'text-slate-400 hover:text-slate-100'
            }`}
          >
            {range}
          </button>
        ))}
      </div>
    </>
  );
}
