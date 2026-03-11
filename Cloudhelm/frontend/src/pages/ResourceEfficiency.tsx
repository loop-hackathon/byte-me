/**
 * Resource Efficiency page for CloudHelm.
 * Displays waste scores, rightsizing recommendations, and scheduling opportunities.
 * Adapted from Loop_ResourceDashboard with CloudHelm design system.
 * OPTIMIZED: Added caching and reduced API calls.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Resource, Recommendation, DashboardStats, ResourceFilters, WasteScoreData } from '../types/resource';
import { api } from '../lib/api';
import { StatCard } from '../components/resource-efficiency/StatCard';
import { Filters } from '../components/resource-efficiency/Filters';
import { WasteScoreChart } from '../components/resource-efficiency/WasteScoreChart';
import { UnderutilizedVMsList } from '../components/resource-efficiency/UnderutilizedVMsList';
import { RightsizingSuggestions } from '../components/resource-efficiency/RightsizingSuggestions';
import { ScheduleRecommendations } from '../components/resource-efficiency/ScheduleRecommendations';
import { LoadingSpinner } from '../components/resource-efficiency/LoadingState';

// Cache duration: 5 minutes
const CACHE_DURATION = 5 * 60 * 1000;

interface CachedData {
  data: any;
  timestamp: number;
}

const cache: Record<string, CachedData> = {};

function getCachedData(key: string): any | null {
  const cached = cache[key];
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  return null;
}

function setCachedData(key: string, data: any): void {
  cache[key] = {
    data,
    timestamp: Date.now()
  };
}

export default function ResourceEfficiency() {
  const [activeTab, setActiveTab] = useState<'overview' | 'underutilized' | 'rightsizing' | 'scheduling'>('overview');
  const [filters, setFilters] = useState<ResourceFilters>({});
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Extract unique teams and environments for filters - memoized
  const teams = useMemo(() => 
    Array.from(new Set(resources.map(r => r.team))).sort(),
    [resources]
  );
  
  const environments = useMemo(() => 
    Array.from(new Set(resources.map(r => r.environment))).sort(),
    [resources]
  );

  // Generate waste score trend data - memoized
  const wasteScoreData = useMemo<WasteScoreData[]>(() => {
    if (!stats) return [];
    
    const avgScore = stats.average_waste_score;
    return [
      { date: 'Mon', score: Math.max(0, avgScore - 5) },
      { date: 'Tue', score: Math.max(0, avgScore - 2) },
      { date: 'Wed', score: avgScore },
      { date: 'Thu', score: Math.max(0, avgScore + 1) },
      { date: 'Fri', score: Math.max(0, avgScore - 3) },
      { date: 'Sat', score: Math.max(0, avgScore - 8) },
      { date: 'Sun', score: Math.max(0, avgScore - 10) },
    ];
  }, [stats]);

  // Load data with caching
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query params
      const params = new URLSearchParams();
      if (filters.team) params.append('team', filters.team);
      if (filters.environment) params.append('environment', filters.environment);
      if (filters.search) params.append('search', filters.search);
      if (filters.min_waste_score !== undefined) params.append('min_waste_score', filters.min_waste_score.toString());

      const cacheKey = `resource-efficiency-${params.toString()}`;
      
      // Check cache first
      const cachedData = getCachedData(cacheKey);
      if (cachedData) {
        setStats(cachedData.stats);
        setResources(cachedData.resources);
        setRecommendations(cachedData.recommendations);
        setLoading(false);
        return;
      }

      // Fetch all data in parallel
      const [statsData, resourcesData, recommendationsData] = await Promise.all([
        api.getResourceStats(params.toString()),
        api.listResources(params.toString()),
        api.listRecommendations(params.toString())
      ]);

      // Cache the results
      setCachedData(cacheKey, {
        stats: statsData,
        resources: resourcesData,
        recommendations: recommendationsData
      });

      setStats(statsData);
      setResources(resourcesData);
      setRecommendations(recommendationsData);

    } catch (err: any) {
      console.error('Error loading resource efficiency data:', err);
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Load data on mount and when filters change
  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFilterChange = useCallback((newFilters: ResourceFilters) => {
    setFilters(newFilters);
  }, []);

  if (loading && !stats) {
    return (
      <div className="p-6 min-h-screen bg-[#020204]">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-6">Resource Efficiency</h1>
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 min-h-screen bg-[#020204]">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Resource Efficiency</h1>
          <p className="text-slate-400">Monitor and optimize your cloud resource utilization</p>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <div className="flex gap-3">
              <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-red-400">Error loading data</p>
                <p className="text-sm text-red-300">{error}</p>
                <button 
                  onClick={loadData}
                  className="mt-2 text-sm text-red-400 hover:text-red-300 underline"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <Filters
          filters={filters}
          onFilterChange={handleFilterChange}
          teams={teams}
          environments={environments}
        />

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Average Waste Score"
            value={`${stats?.average_waste_score.toFixed(1) || 0}%`}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            valueColor={stats && stats.average_waste_score > 50 ? 'text-red-400' : 'text-green-400'}
          />
          <StatCard
            title="Underutilized VMs"
            value={stats?.underutilized_vms.toString() || '0'}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
              </svg>
            }
            valueColor="text-yellow-400"
          />
          <StatCard
            title="Potential Savings"
            value={`$${((stats?.potential_savings || 0) / 1000).toFixed(1)}k`}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            valueColor="text-emerald-400"
          />
          <StatCard
            title="Schedulable Resources"
            value={stats?.schedulable_resources.toString() || '0'}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            valueColor="text-cyan-400"
          />
        </div>

        {/* Tabs */}
        <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl">
          <div className="border-b border-slate-700">
            <div className="flex gap-2 p-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'overview'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('underutilized')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'underutilized'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                Underutilized VMs
              </button>
              <button
                onClick={() => setActiveTab('rightsizing')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'rightsizing'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                Rightsizing
              </button>
              <button
                onClick={() => setActiveTab('scheduling')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'scheduling'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                Scheduling
              </button>
            </div>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <WasteScoreChart data={wasteScoreData} loading={loading} />
            )}

            {activeTab === 'underutilized' && (
              <UnderutilizedVMsList resources={resources} loading={loading} />
            )}

            {activeTab === 'rightsizing' && (
              <RightsizingSuggestions recommendations={recommendations} loading={loading} />
            )}

            {activeTab === 'scheduling' && (
              <ScheduleRecommendations recommendations={recommendations} loading={loading} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
