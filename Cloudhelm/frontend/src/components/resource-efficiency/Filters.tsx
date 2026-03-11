/**
 * Filters component for resource efficiency dashboard.
 * Matches CloudHelm design system.
 */
import React from 'react';
import type { ResourceFilters } from '../../types/resource';

interface FiltersProps {
  filters: ResourceFilters;
  onFilterChange: (filters: ResourceFilters) => void;
  teams: string[];
  environments: string[];
}

export const Filters: React.FC<FiltersProps> = ({
  filters,
  onFilterChange,
  teams,
  environments
}) => {
  const handleTeamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ ...filters, team: e.target.value || undefined });
  };

  const handleEnvironmentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ ...filters, environment: e.target.value || undefined });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, search: e.target.value || undefined });
  };

  const handleWasteScoreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value ? parseFloat(e.target.value) : undefined;
    onFilterChange({ ...filters, min_waste_score: value });
  };

  const handleReset = () => {
    onFilterChange({});
  };

  const hasActiveFilters = filters.team || filters.environment || filters.search || filters.min_waste_score !== undefined;

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            Reset All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Team Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Team
          </label>
          <select
            value={filters.team || ''}
            onChange={handleTeamChange}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          >
            <option value="">All Teams</option>
            {teams.map(team => (
              <option key={team} value={team}>{team}</option>
            ))}
          </select>
        </div>

        {/* Environment Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Environment
          </label>
          <select
            value={filters.environment || ''}
            onChange={handleEnvironmentChange}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          >
            <option value="">All Environments</option>
            {environments.map(env => (
              <option key={env} value={env}>{env}</option>
            ))}
          </select>
        </div>

        {/* Search Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Search
          </label>
          <input
            type="text"
            value={filters.search || ''}
            onChange={handleSearchChange}
            placeholder="Search by name..."
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-50 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          />
        </div>

        {/* Min Waste Score Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Min Waste Score
          </label>
          <input
            type="number"
            value={filters.min_waste_score ?? ''}
            onChange={handleWasteScoreChange}
            placeholder="0-100"
            min="0"
            max="100"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-50 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  );
};
