/**
 * Loading state components for resource efficiency dashboard.
 * Matches CloudHelm design system.
 */
import React from 'react';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
    </div>
  );
};

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="bg-slate-800/60 h-32 rounded-xl"></div>
      <div className="bg-slate-800/60 h-32 rounded-xl"></div>
      <div className="bg-slate-800/60 h-32 rounded-xl"></div>
    </div>
  );
};

export const EmptyState: React.FC<{ message: string; icon?: React.ReactNode }> = ({ message, icon }) => {
  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
      {icon && <div className="flex justify-center mb-4 text-slate-500">{icon}</div>}
      <p className="text-slate-400">{message}</p>
    </div>
  );
};
