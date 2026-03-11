import React from 'react';
import type { CostSummaryResponse, BudgetStatus } from '../../types/cost';

interface CostSummaryCardsProps {
  costData: CostSummaryResponse | null;
  budgets: BudgetStatus[];
  anomalyCount: number;
  loading?: boolean;
}

export default function CostSummaryCards({
  costData,
  budgets,
  anomalyCount,
  loading = false
}: CostSummaryCardsProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const teamsAtRisk = budgets.filter(
    b => b.status === 'AT_RISK' || b.status === 'OVER'
  ).length;

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-slate-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      {/* Total Spend Card */}
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 hover:bg-slate-800/60 transition-all duration-300">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-slate-300">Total Spend</h3>
          <span className="text-2xl">💰</span>
        </div>
        <p className="text-3xl font-bold text-slate-100">
          {costData ? formatCurrency(costData.total_cost) : '$0'}
        </p>
        <p className="text-sm text-slate-400 mt-2">
          {costData ? `${costData.from} to ${costData.to}` : 'No data'}
        </p>
      </div>

      {/* Active Anomalies Card */}
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 hover:bg-slate-800/60 transition-all duration-300">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-slate-300">Active Anomalies</h3>
          <span className="text-2xl">🚨</span>
        </div>
        <p className="text-3xl font-bold text-slate-100">{anomalyCount}</p>
        <p className="text-sm text-slate-400 mt-2">
          {anomalyCount === 0 ? 'No anomalies detected' : 'Unusual spending patterns'}
        </p>
      </div>

      {/* Teams at Risk Card */}
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 hover:bg-slate-800/60 transition-all duration-300">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-slate-300">Teams at Risk</h3>
          <span className="text-2xl">⚠️</span>
        </div>
        <p className="text-3xl font-bold text-slate-100">{teamsAtRisk}</p>
        <p className="text-sm text-slate-400 mt-2">
          {teamsAtRisk === 0 ? 'All budgets on track' : 'Over or near budget'}
        </p>
      </div>
    </div>
  );
}
