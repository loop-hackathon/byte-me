/**
 * Schedule Recommendations component.
 * Displays automated start/stop schedule suggestions.
 * Matches CloudHelm design system.
 */
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { Recommendation } from '../../types/resource';
import { LoadingSkeleton, EmptyState } from './LoadingState';

interface ScheduleRecommendationsProps {
  recommendations: Recommendation[];
  loading: boolean;
}

export const ScheduleRecommendations: React.FC<ScheduleRecommendationsProps> = ({ recommendations, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Schedule Recommendations</h3>
        <LoadingSkeleton />
      </div>
    );
  }

  // Filter schedule recommendations
  const schedules = recommendations.filter(r => r.recommendation_type === 'schedule');

  if (schedules.length === 0) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Schedule Recommendations</h3>
        <EmptyState 
          message="No schedulable resources found"
          icon={
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>
    );
  }

  // Generate mock hourly utilization pattern for visualization
  const generateUtilizationPattern = () => {
    return [
      { hour: '00:00', utilization: 5 },
      { hour: '04:00', utilization: 3 },
      { hour: '08:00', utilization: 45 },
      { hour: '12:00', utilization: 72 },
      { hour: '16:00', utilization: 68 },
      { hour: '20:00', utilization: 20 },
      { hour: '23:00', utilization: 2 },
    ];
  };

  const totalSavings = schedules.reduce((sum, r) => sum + r.potential_savings, 0);

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Schedule Recommendations</h3>
        <p className="text-sm text-slate-400">Automated start/stop schedules for non-production resources</p>
      </div>

      <div className="space-y-6">
        {schedules.map((rec) => {
          const utilizationData = generateUtilizationPattern();
          const idlePercentage = 65; // Mock value

          return (
            <div key={rec.id} className="rounded-lg border border-slate-800 bg-slate-800/50 p-4">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h4 className="font-semibold text-white">{rec.resource_name || rec.resource_id}</h4>
                    <p className="text-sm text-slate-400">{rec.description}</p>
                  </div>
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 w-fit">
                    {idlePercentage}% Idle Time
                  </span>
                </div>

                {/* Recommended Schedule */}
                <div className="bg-slate-700 rounded-lg p-3">
                  <p className="text-sm font-medium text-slate-400 mb-1">Recommended Schedule</p>
                  <p className="text-sm font-mono font-semibold text-white">{rec.suggested_action}</p>
                </div>

                {/* Utilization Chart */}
                <div>
                  <p className="text-sm font-medium text-slate-400 mb-2">Hourly Utilization Pattern</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={utilizationData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis 
                        dataKey="hour" 
                        stroke="#94a3b8" 
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis 
                        stroke="#94a3b8" 
                        style={{ fontSize: '12px' }}
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
                        dataKey="utilization"
                        stroke="#22d3ee"
                        dot={false}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Savings Info */}
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-400">Idle Time</p>
                    <p className="font-semibold text-white">{idlePercentage}%</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-400">Monthly Savings</p>
                    <p className="font-semibold text-emerald-400">${rec.potential_savings.toFixed(2)}</p>
                  </div>
                  <div className="space-y-1 col-span-2 md:col-span-1">
                    <p className="text-xs font-medium text-slate-400">Annual Savings</p>
                    <p className="font-semibold text-emerald-400">${(rec.potential_savings * 12).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* Best Practices */}
        <div className="mt-6 rounded-lg bg-amber-500/10 p-4 border border-amber-500/30">
          <div className="flex gap-3">
            <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-amber-200">
              <p className="font-semibold mb-1">Scheduling Best Practices</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Schedules are applied only to non-production environments</li>
                <li>Always test schedules in staging before production</li>
                <li>Consider time zones and team working hours</li>
                <li>Total potential annual savings: <span className="font-bold text-amber-300">${(totalSavings * 12).toFixed(2)}</span></li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
