import React from 'react';
import type { CostAnomaly } from '../../types/cost';

interface CostAnomaliesTableProps {
  anomalies: CostAnomaly[];
  loading?: boolean;
}

export default function CostAnomaliesTable({ anomalies, loading = false }: CostAnomaliesTableProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
      medium: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
      high: 'bg-red-500/20 text-red-300 border border-red-500/30'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[severity as keyof typeof colors]}`}>
        {severity.toUpperCase()}
      </span>
    );
  };

  const getDirectionIcon = (direction: string) => {
    return direction === 'spike' ? '📈' : '📉';
  };

  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">Cost Anomalies</h3>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-100">Cost Anomalies</h3>
        <span className="text-sm text-slate-400">{anomalies.length} detected</span>
      </div>

      {anomalies.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <p className="text-lg mb-2">🎉 No anomalies detected</p>
          <p className="text-sm">Your spending patterns look normal</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/5">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Cloud
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Team
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Service
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Env
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Expected
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Actual
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Direction
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Severity
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {anomalies.map((anomaly) => (
                <tr key={anomaly.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-white">
                    {formatDate(anomaly.ts_date)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-white">
                    <span className="uppercase font-medium">{anomaly.cloud}</span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-white">
                    {anomaly.team || '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-white">
                    {anomaly.service || '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-white">
                    {anomaly.env || '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-slate-400 text-right">
                    {formatCurrency(anomaly.expected_cost)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-white text-right">
                    {formatCurrency(anomaly.actual_cost)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center text-lg">
                    {getDirectionIcon(anomaly.direction)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    {getSeverityBadge(anomaly.severity)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
