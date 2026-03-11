/**
 * Rightsizing Suggestions component.
 * Displays instance type recommendations.
 * Matches CloudHelm design system.
 */
import React from 'react';
import type { Recommendation } from '../../types/resource';
import { LoadingSkeleton, EmptyState } from './LoadingState';

interface RightsizingSuggestionsProps {
  recommendations: Recommendation[];
  loading: boolean;
}

export const RightsizingSuggestions: React.FC<RightsizingSuggestionsProps> = ({ recommendations, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Rightsizing Suggestions</h3>
        <LoadingSkeleton />
      </div>
    );
  }

  // Filter and sort by monthly savings descending
  const rightsizing = recommendations
    .filter(r => r.recommendation_type === 'rightsizing')
    .sort((a, b) => b.potential_savings - a.potential_savings);

  if (rightsizing.length === 0) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Rightsizing Suggestions</h3>
        <EmptyState 
          message="All resources appear to be optimally sized"
          icon={
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>
    );
  }

  const totalSavings = rightsizing.reduce((sum, r) => sum + r.potential_savings, 0);

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Rightsizing Suggestions</h3>
        <p className="text-sm text-slate-400">Instance type recommendations based on utilization analysis</p>
      </div>

      <div className="space-y-4">
        {rightsizing.map((rec) => (
          <div
            key={rec.id}
            className="rounded-lg border border-slate-800 bg-slate-800/50 p-4 hover:border-slate-700 hover:bg-slate-800 transition-colors"
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between mb-3">
              <div className="space-y-2 flex-1">
                <h4 className="font-semibold text-white">{rec.resource_name || rec.resource_id}</h4>
                <p className="text-sm text-slate-400">{rec.description}</p>
              </div>
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-slate-700 border border-slate-600 text-slate-200 w-fit">
                {(rec.confidence * 100).toFixed(0)}% Confidence
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 mb-3">
              <div className="space-y-1">
                <p className="text-xs font-medium text-slate-400">Suggested Action</p>
                <p className="text-sm font-semibold text-emerald-400">{rec.suggested_action}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-slate-400">Monthly Savings</p>
                <p className="text-sm font-bold text-emerald-400">${rec.potential_savings.toFixed(2)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-slate-400">Annual Savings</p>
                <p className="text-sm font-bold text-emerald-400">${(rec.potential_savings * 12).toFixed(2)}</p>
              </div>
            </div>
          </div>
        ))}

        {/* Total Savings Summary */}
        <div className="mt-6 rounded-lg bg-cyan-500/10 p-4 border border-cyan-500/30">
          <div className="flex gap-3">
            <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-cyan-200">
              <p className="font-semibold mb-1">Potential Annual Savings</p>
              <p>
                Following these {rightsizing.length} recommendations could save approximately{' '}
                <span className="font-bold text-cyan-300">
                  ${(totalSavings * 12).toFixed(2)}
                </span>{' '}
                annually.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
