/**
 * Underutilized VMs List component.
 * Displays resources with waste score > 30%.
 * Matches CloudHelm design system.
 */
import React from 'react';
import type { Resource } from '../../types/resource';
import { LoadingSkeleton, EmptyState } from './LoadingState';

interface UnderutilizedVMsListProps {
  resources: Resource[];
  loading: boolean;
}

export const UnderutilizedVMsList: React.FC<UnderutilizedVMsListProps> = ({ resources, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Underutilized Resources</h3>
        <LoadingSkeleton />
      </div>
    );
  }

  // Filter resources with waste score > 30% and sort by waste score descending
  const underutilized = resources
    .filter(r => r.waste_score > 30)
    .sort((a, b) => b.waste_score - a.waste_score);

  if (underutilized.length === 0) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Underutilized Resources</h3>
        <EmptyState 
          message="No underutilized resources found (waste score > 30%)"
          icon={
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>
    );
  }

  const getUtilizationColor = (value: number) => {
    if (value < 20) return 'bg-red-500/10 text-red-400 border-red-500/30';
    if (value < 40) return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
    if (value < 60) return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
    return 'bg-green-500/10 text-green-400 border-green-500/30';
  };

  const calculateMonthlyWaste = (wasteScore: number) => {
    // Estimate: $500/month per resource * waste_score/100
    return Math.round((wasteScore / 100) * 500);
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Underutilized Resources</h3>
        <p className="text-sm text-slate-400">Resources with waste score &gt; 30%</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Name</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">CPU %</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">Memory %</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">Waste Score</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Environment</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Team</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">Monthly Waste</th>
            </tr>
          </thead>
          <tbody>
            {underutilized.map((resource) => (
              <tr key={resource.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                <td className="py-3 px-4">
                  <div>
                    <p className="text-sm font-medium text-white">{resource.name}</p>
                    <p className="text-xs text-slate-500">{resource.resource_type}</p>
                  </div>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getUtilizationColor(resource.avg_cpu || 0)}`}>
                    {resource.avg_cpu?.toFixed(1) || 'N/A'}%
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getUtilizationColor(resource.avg_memory || 0)}`}>
                    {resource.avg_memory?.toFixed(1) || 'N/A'}%
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border bg-red-500/10 text-red-400 border-red-500/30">
                    {resource.waste_score.toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-slate-800/60 border border-slate-700 text-slate-300">
                    {resource.environment}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-slate-800 text-slate-300">
                    {resource.team}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="text-sm font-semibold text-emerald-400">
                    ${calculateMonthlyWaste(resource.waste_score)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
