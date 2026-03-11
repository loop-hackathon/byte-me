/**
 * StatCard component for displaying dashboard statistics.
 * Matches CloudHelm design system.
 */
import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: 'positive' | 'negative' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  valueColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  trendValue,
  icon,
  valueColor = 'text-white'
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'positive':
        return 'text-green-400';
      case 'negative':
        return 'text-red-400';
      case 'neutral':
        return 'text-slate-400';
      default:
        return 'text-slate-400';
    }
  };

  const getTrendIcon = () => {
    if (!trend || trend === 'neutral') return null;
    
    return trend === 'positive' ? (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    ) : (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    );
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm text-slate-400">{title}</p>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      
      <div className="flex items-baseline gap-2">
        <p className={`text-3xl font-bold ${valueColor}`}>{value}</p>
        
        {trendValue && (
          <div className={`flex items-center gap-1 text-sm ${getTrendColor()}`}>
            {getTrendIcon()}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
};
