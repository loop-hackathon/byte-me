/**
 * Waste Score Chart component showing 7-day trend.
 * Matches CloudHelm design system.
 */
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { LoadingSkeleton, EmptyState } from './LoadingState';

interface WasteScoreData {
  date: string;
  score: number;
}

interface WasteScoreChartProps {
  data: WasteScoreData[];
  loading: boolean;
}

export const WasteScoreChart: React.FC<WasteScoreChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Waste Score Trend (7 Days)</h3>
        <LoadingSkeleton />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Waste Score Trend (7 Days)</h3>
        <EmptyState message="No waste score data available" />
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Waste Score Trend (7 Days)</h3>
        <p className="text-sm text-slate-400">Average waste score across all resources</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="date" 
            stroke="#94a3b8" 
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#94a3b8" 
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#f1f5f9',
            }}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Line 
            type="monotone" 
            dataKey="score" 
            stroke="#22d3ee" 
            strokeWidth={2}
            dot={{ fill: '#22d3ee', r: 4 }}
            activeDot={{ r: 6 }}
            name="Waste Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
