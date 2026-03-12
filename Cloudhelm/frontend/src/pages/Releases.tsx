import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend
} from 'recharts';
import type { Repository, Release, Vulnerability } from '../types/release';
import { api } from '../lib/api';
import CloudHelmAssistant from '../components/CloudHelmAssistant';

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

// Helper functions - memoized
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

const formatTimeAgo = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'just now';
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
};

const truncate = (str: string, length: number): string => {
  if (!str) return '';
  return str.length <= length ? str : str.slice(0, length) + '...';
};

// Risk Badge Component - CloudHelm styled
const RiskBadge: React.FC<{ level: 'Healthy' | 'Suspect' | 'Risky'; size?: 'sm' | 'md' }> = ({ level, size = 'md' }) => {
  const styles = {
    Healthy: 'bg-green-500/10 text-green-400 border-green-500/30',
    Suspect: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    Risky: 'bg-red-500/10 text-red-400 border-red-500/30',
  };
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';
  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${styles[level]} ${sizeClasses}`}>
      {level}
    </span>
  );
};

// Badge Component - CloudHelm styled
const Badge: React.FC<{ variant: 'success' | 'danger' | 'warning' | 'info'; children: React.ReactNode }> = ({ variant, children }) => {
  const styles = {
    success: 'bg-green-500/10 text-green-400 border-green-500/30',
    danger: 'bg-red-500/10 text-red-400 border-red-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[variant]}`}>
      {children}
    </span>
  );
};

const VulnerabilityItem: React.FC<{ 
  vulnerability: Vulnerability; 
  isExpanded: boolean; 
  onToggle: () => void 
}> = ({ vulnerability, isExpanded, onToggle }) => {
  const severityColors = {
    CRITICAL: 'bg-red-600 text-white font-black',
    HIGH: 'bg-orange-600 text-white font-bold',
    MEDIUM: 'bg-yellow-600 text-white',
    LOW: 'bg-blue-600 text-white',
    UNKNOWN: 'bg-gray-600 text-white',
  }[vulnerability.severity] || 'bg-gray-600 text-white';

  return (
    <div className="border-b border-slate-800 last:border-0">
      <div 
        className="flex items-center py-4 px-4 hover:bg-slate-800/30 cursor-pointer transition-colors"
        onClick={onToggle}
      >
        <div className={`w-24 text-center py-1 rounded text-[10px] uppercase mr-6 ${severityColors}`}>
          {vulnerability.severity}
        </div>
        <div className="w-40 text-sm font-mono text-slate-300 mr-6">
          {vulnerability.id}
        </div>
        <div className="flex-1 text-sm text-white">
          {vulnerability.package_name}
        </div>
        <div className="text-slate-500">
          <svg className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {isExpanded && (
        <div className="px-4 pb-6 pt-2 bg-slate-800/20">
          <div className="pl-30 md:pl-76">
            <h4 className="text-lg font-bold text-white mb-2">
              {vulnerability.title || vulnerability.package_name}
            </h4>
            <p className="text-slate-400 text-sm mb-4 leading-relaxed">
              {vulnerability.description || 'No description provided.'}
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 border-t border-slate-700/50 pt-4">
              <div className="flex text-sm">
                <span className="w-32 text-slate-500">Package Name:</span>
                <span className="text-slate-200">{vulnerability.package_name}</span>
              </div>
              <div className="flex text-sm">
                <span className="w-32 text-slate-500">Installed Version:</span>
                <span className="font-mono text-cyan-400">{vulnerability.installed_version}</span>
              </div>
              <div className="flex text-sm">
                <span className="w-32 text-slate-500">Fixed Version:</span>
                <span className="font-mono text-green-400">{vulnerability.fixed_version || 'N/A'}</span>
              </div>
              <div className="flex text-sm">
                <span className="w-32 text-slate-500">More Info:</span>
                {vulnerability.primary_url ? (
                  <a 
                    href={vulnerability.primary_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-cyan-400 hover:underline break-all"
                  >
                    {vulnerability.primary_url}
                  </a>
                ) : (
                  <span className="text-slate-500 italic">No link available</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function Releases() {
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [selectedReleaseId, setSelectedReleaseId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [securityScan, setSecurityScan] = useState<any>(null);
  const [scanning, setScanning] = useState(false);
  const [vulnFilter, setVulnFilter] = useState<string>('ALL');
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);
  const [showSBOM, setShowSBOM] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const selectedRelease = useMemo(() => 
    releases.find(r => r.id === selectedReleaseId) || releases[0],
    [selectedReleaseId, releases]
  );

  const previousRelease = useMemo(() => {
    if (!selectedReleaseId) return null;
    const index = releases.findIndex(r => r.id === selectedReleaseId);
    return index < releases.length - 1 ? releases[index + 1] : null;
  }, [selectedReleaseId, releases]);

  // Memoized stats calculation
  const stats = useMemo(() => ({

    total: releases.length,
    healthy: releases.filter(r => r.risk_level === 'Healthy').length,
    suspect: releases.filter(r => r.risk_level === 'Suspect').length,
    risky: releases.filter(r => r.risk_level === 'Risky').length,
    scanned: releases.filter(r => (r.critical_vulns || 0) + (r.high_vulns || 0) + (r.medium_vulns || 0) + (r.low_vulns || 0) > 0).length,
  }), [releases]);

  const securityTrendData = useMemo(() => {
    return [...releases]
      .reverse()
      .filter(r => (r.critical_vulns || 0) + (r.high_vulns || 0) + (r.medium_vulns || 0) + (r.low_vulns || 0) > 0)
      .slice(-10)
      .map(r => ({
        name: `v${r.version}`,
        critical: r.critical_vulns || 0,
        high: r.high_vulns || 0,
        medium: r.medium_vulns || 0,
        low: r.low_vulns || 0,
        risk: r.risk_score
      }));
  }, [releases]);

  const currentRepo = useMemo(() => 
    selectedRepo ? repositories.find(r => r.id === selectedRepo) : null,
    [selectedRepo, repositories]
  );

  // Load repositories with caching
  const loadRepositories = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const cacheKey = 'repositories-list';
      const cachedData = getCachedData(cacheKey);
      
      if (cachedData) {
        setRepositories(cachedData);
        setLoading(false);
        return;
      }
      
      const repos = await api.listRepositories();
      setCachedData(cacheKey, repos);
      setRepositories(repos);
    } catch (err: any) {
      setError(err.message || 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load releases with caching
  const loadReleases = useCallback(async (repoId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const cacheKey = `releases-${repoId}`;
      const cachedData = getCachedData(cacheKey);
      
      if (cachedData) {
        setReleases(cachedData);
        setLoading(false);
        return;
      }
      
      // First, try to get existing releases
      let repoReleases = await api.getRepositoryReleases(repoId);
      
      // If no releases found, try to sync from GitHub
      if (repoReleases.length === 0) {
        try {
          await api.syncRepositoryReleases(repoId);
          // Fetch again after sync
          repoReleases = await api.getRepositoryReleases(repoId);
        } catch (syncErr: any) {
          console.warn('Could not sync releases:', syncErr);
          // Continue with empty releases
        }
      }
      
      setCachedData(cacheKey, repoReleases);
      setReleases(repoReleases);
    } catch (err: any) {
      setError(err.message || 'Failed to load releases');
      setReleases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Run security scan
  const runSecurityScan = useCallback(async (repoId: string, ref?: string) => {
    try {
      setScanning(true);
      const result = await api.scanRepositorySecurity(repoId, ref);
      setSecurityScan(result.results);
    } catch (err: any) {
      console.error('Security scan failed:', err);
    } finally {
      setScanning(false);
    }
  }, []);

  // Load repositories on mount
  useEffect(() => {
    loadRepositories();
  }, [loadRepositories]);

  // Load releases and trigger security scan when repository is selected
  useEffect(() => {
    const initRepoView = async () => {
      if (selectedRepo) {
        // Reset scan results when changing repo
        setSecurityScan(null);
        setExpandedVuln(null);
        setVulnFilter('ALL');
        setSelectedReleaseId(null);
        
        // Load releases first to get the latest commit for security scan
        await loadReleases(selectedRepo);
        
        // We need to get the latest releases directly here because the state update 
        // might not have propagated yet for the subsequent runSecurityScan call
        const repoReleases = await api.getRepositoryReleases(selectedRepo);
        const latestCommit = repoReleases.length > 0 ? repoReleases[0].commit : undefined;
        
        if (latestCommit) {
           runSecurityScan(selectedRepo, latestCommit);
        }
      }
    };
    
    initRepoView();
  }, [selectedRepo, loadReleases, runSecurityScan]);

  const handleReleaseClick = useCallback((release: Release) => {
    setSelectedReleaseId(release.id);
    setSecurityScan(null);
    runSecurityScan(selectedRepo!, release.commit);
  }, [selectedRepo, runSecurityScan]);

  const handleSyncRepositories = useCallback(async () => {
    try {
      setSyncing(true);
      setError(null);
      // Clear cache
      delete cache['repositories-list'];
      await api.syncRepositories();
      await loadRepositories();
    } catch (err: any) {
      setError(err.message || 'Failed to sync repositories');
    } finally {
      setSyncing(false);
    }
  }, [loadRepositories]);

  const handleSyncReleases = useCallback(async () => {
    if (!selectedRepo) return;
    
    try {
      setSyncing(true);
      setError(null);
      // Clear cache
      delete cache[`releases-${selectedRepo}`];
      await api.syncRepositoryReleases(selectedRepo);
      await loadReleases(selectedRepo);
    } catch (err: any) {
      setError(err.message || 'Failed to sync releases');
    } finally {
      setSyncing(false);
    }
  }, [selectedRepo, loadReleases]);

  if (!selectedRepo) {
    // Repository Selection View
    return (
      <div className="p-6 min-h-screen bg-[#020204]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Releases</h1>
              <p className="text-slate-400">Track software releases and analyze their impact</p>
            </div>
            <button
              onClick={handleSyncRepositories}
              disabled={syncing}
              className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2"
            >
              {syncing ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Syncing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Sync from GitHub
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
            </div>
          ) : repositories.length === 0 ? (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
              <p className="text-slate-400 mb-4">No repositories found. Sync from GitHub to get started.</p>
              <button
                onClick={handleSyncRepositories}
                className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-medium transition-colors"
              >
                Sync from GitHub
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {repositories.map((repo) => (
                <div
                  key={repo.id}
                  onClick={() => setSelectedRepo(repo.id)}
                  className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 cursor-pointer hover:bg-slate-900/80 hover:border-cyan-400/50 transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white mb-1">{repo.name}</h3>
                      <p className="text-sm text-slate-500 font-mono">{repo.full_name}</p>
                    </div>
                    {repo.language && (
                      <span className="px-2 py-1 bg-slate-800/60 border border-slate-700 rounded text-xs text-slate-400">
                        {repo.language}
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="text-sm text-slate-300 mb-4 line-clamp-2">{repo.description}</p>
                  )}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center text-slate-400">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {repo.stars}
                    </div>
                    <div className="text-slate-400">
                      {repo.last_deployment ? formatTimeAgo(repo.last_deployment) : 'No deployments'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Release Dashboard View
  return (
    <div className="p-6 min-h-screen bg-[#020204]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => setSelectedRepo(null)}
            className="text-cyan-400 hover:text-cyan-300 font-medium mb-4 inline-flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to repositories
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{currentRepo?.name}</h1>
              <p className="text-slate-400">{currentRepo?.description}</p>
              <p className="text-sm text-slate-500 font-mono mt-1">{currentRepo?.full_name}</p>
            </div>
            <div className="flex gap-3 items-center">
              <button
                onClick={handleSyncReleases}
                disabled={syncing}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2"
              >
                {syncing ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Syncing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Sync Releases
                  </>
                )}
              </button>
              <div className="flex gap-2 bg-slate-800/40 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'grid' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Grid
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'list' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  List
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <p className="text-sm text-slate-400 mb-1">Total Releases</p>
            <p className="text-3xl font-bold text-white">{stats.total}</p>
          </div>
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <p className="text-sm text-slate-400 mb-1">Healthy</p>
            <p className="text-3xl font-bold text-green-400">{stats.healthy}</p>
          </div>
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <p className="text-sm text-slate-400 mb-1">Risky</p>
            <p className="text-3xl font-bold text-red-400">{stats.risky}</p>
          </div>
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <p className="text-sm text-slate-400 mb-1">Security Score</p>
            <p className={`text-3xl font-bold ${
              securityScan ? (
                securityScan.risk_score < 30 ? 'text-green-400' :
                securityScan.risk_score < 70 ? 'text-yellow-400' : 'text-red-400'
              ) : 'text-slate-500'
            }`}>
              {scanning ? '...' : securityScan ? `${Math.round(securityScan.risk_score)}%` : 'N/A'}
            </p>
          </div>
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <p className="text-sm text-slate-400 mb-1">Scanned Versions</p>
            <p className="text-3xl font-bold text-cyan-400">
              {stats.scanned} <span className="text-sm font-normal text-slate-500">/ {stats.total}</span>
            </p>
          </div>
        </div>

        {/* Security Trend Chart */}
        {securityTrendData.length > 0 && (
          <div className="mb-8 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
                Security Posture History
              </h2>
              <div className="flex gap-4 text-xs">
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"/> Critical</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500"/> High</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"/> Medium</div>
              </div>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={securityTrendData}>
                  <defs>
                    <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                    itemStyle={{ fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="critical" stroke="#ef4444" fillOpacity={1} fill="url(#colorCritical)" strokeWidth={2} />
                  <Area type="monotone" dataKey="high" stroke="#f97316" fill="transparent" strokeWidth={2} />
                  <Area type="monotone" dataKey="medium" stroke="#eab308" fill="transparent" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Security Scan Results */}
        {securityScan && (
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 mb-8 overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white flex items-center">
                <svg className="w-6 h-6 mr-2 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.040L3 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622l-0.382-3.016z" />
                </svg>
                Vulnerability Scan Results {selectedRelease && `(v${selectedRelease.version})`}
              </h3>
              <div className="flex gap-2">
                {previousRelease && (
                  <div className="flex items-center gap-1 text-[10px] uppercase font-bold text-slate-500 mr-2 bg-slate-800/50 px-2 py-1 rounded">
                    Comparing v{selectedRelease?.version} ↔ v{previousRelease.version}
                  </div>
                )}
                <button 
                  onClick={() => setShowSBOM(true)}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors"
                >
                  Generate SBOM Output
                </button>
              </div>
            </div>

            {previousRelease && (previousRelease.critical_vulns || 0) > 0 && (
              <div className="mb-6 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 flex items-center justify-between">
                <div className="text-sm text-slate-300">
                  <span className="font-bold text-blue-400">Progression Analysis:</span>{' '}
                  { (selectedRelease?.critical_vulns || 0) < (previousRelease.critical_vulns || 0) ? (
                    <span className="text-green-400">Security Improved! { (previousRelease.critical_vulns || 0) - (selectedRelease?.critical_vulns || 0) } critical vulnerabilities fixed since v{previousRelease.version}.</span>
                  ) : (selectedRelease?.critical_vulns || 0) > (previousRelease.critical_vulns || 0) ? (
                    <span className="text-red-400">Security Warning: { (selectedRelease?.critical_vulns || 0) - (previousRelease.critical_vulns || 0) } new critical vulnerabilities introduced since v{previousRelease.version}.</span>
                  ) : (
                    <span>Stability maintained: Critical vulnerability count unchanged since v{previousRelease.version}.</span>
                  )}
                </div>
              </div>
            )}

            {/* Severity Tabs */}
            <div className="flex border-b border-slate-800 mb-6">
              {[
                { id: 'ALL', label: 'ALL', count: securityScan.vulnerabilities?.length || 0 },
                { id: 'CRITICAL', label: 'CRITICAL', count: securityScan.security_metrics.critical },
                { id: 'HIGH', label: 'HIGH', count: securityScan.security_metrics.high },
                { id: 'MEDIUM', label: 'MEDIUM', count: securityScan.security_metrics.medium },
                { id: 'LOW', label: 'LOW', count: securityScan.security_metrics.low },
                { id: 'UNKNOWN', label: 'UNKNOWN', count: securityScan.security_metrics.unknown },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setVulnFilter(tab.id)}
                  className={`px-6 py-3 text-xs font-bold transition-all relative ${
                    vulnFilter === tab.id 
                      ? 'text-white border-b-2 border-red-500' 
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>
            
            <div className="bg-slate-900/40 rounded-lg border border-slate-800">
              <div className="px-4 py-3 border-b border-slate-800 flex text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-slate-800/20">
                <div className="w-24 mr-6">Severity</div>
                <div className="w-40 mr-6">CVE ID</div>
                <div className="flex-1">Package</div>
              </div>
              
              <div className="max-h-[500px] overflow-y-auto">
                {securityScan.vulnerabilities
                  ?.filter((v: any) => vulnFilter === 'ALL' || v.severity === vulnFilter)
                  .map((vuln: any, idx: number) => (
                    <VulnerabilityItem 
                      key={`${vuln.id}-${idx}`}
                      vulnerability={vuln}
                      isExpanded={expandedVuln === `${vuln.id}-${idx}`}
                      onToggle={() => setExpandedVuln(expandedVuln === `${vuln.id}-${idx}` ? null : `${vuln.id}-${idx}`)}
                    />
                  )) || (
                    <div className="py-12 text-center text-slate-500">
                      No vulnerabilities found for this severity level.
                    </div>
                  )}
              </div>
            </div>

            <div className="mt-6 flex justify-between items-center bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
              <div className="flex items-center text-sm text-slate-400">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Scan based on version v{selectedRelease?.version || 'latest'} ({truncate(selectedRelease?.commit || '', 8)})
              </div>
              <button 
                onClick={() => runSecurityScan(selectedRepo!, selectedRelease?.commit)}
                disabled={scanning}
                className="text-cyan-400 hover:text-cyan-300 text-xs font-bold uppercase tracking-widest flex items-center transition-colors"
              >
                <svg className={`w-3 h-3 mr-1 ${scanning ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Rescan This Version
              </button>
            </div>
          </div>
        )}

        {/* SBOM Modal */}
        {showSBOM && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl">
              <div className="flex justify-between items-center p-6 border-b border-slate-800">
                <h3 className="text-xl font-bold text-white">Software Bill of Materials (SBOM)</h3>
                <button onClick={() => setShowSBOM(false)} className="text-slate-400 hover:text-white">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6 overflow-y-auto font-mono text-xs text-cyan-400/80 bg-slate-950/50">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(securityScan?.sbom || { message: "SBOM not available for this scan" }, null, 2)}
                </pre>
              </div>
              <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-900/50">
                <button 
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(securityScan.sbom, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `sbom-${selectedRepo}.json`;
                    a.click();
                  }}
                  className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Download JSON
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Releases List */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-4">Recent Releases / Commits ({releases.length})</h2>
          
          {error && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
            </div>
          ) : releases.length === 0 ? (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
              <p className="text-slate-400">No releases found for this repository.</p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {releases.map((release) => (
                <div
                  key={release.id}
                  onClick={() => handleReleaseClick(release)}
                  className={`bg-slate-900/60 backdrop-blur-lg border rounded-xl p-6 cursor-pointer transition-all ${
                    selectedRelease?.id === release.id ? 'border-cyan-400 ring-1 ring-cyan-400/50' : 'border-slate-700 hover:border-cyan-400/50'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-bold text-white">v{release.version}</h3>
                      <p className="text-sm text-slate-500 font-mono">{truncate(release.commit, 8)}</p>
                      
                      {/* Vulnerability Badges */}
                      {(release.critical_vulns || 0) + (release.high_vulns || 0) > 0 && (
                        <div className="flex gap-2 mt-2">
                          {release.critical_vulns! > 0 && (
                            <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-500 text-[10px] font-bold border border-red-500/30">
                              {release.critical_vulns}C
                            </span>
                          )}
                          {release.high_vulns! > 0 && (
                            <span className="px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-500 text-[10px] font-bold border border-orange-500/30">
                              {release.high_vulns}H
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 flex-col items-end">
                      <RiskBadge level={release.risk_level} size="sm" />
                      <Badge variant={release.status === 'success' ? 'success' : 'danger'}>
                        {release.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm mb-4">
                    <div className="flex items-center text-slate-400">
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {formatDateTime(release.deployed_at)}
                    </div>
                    <div className="flex items-center text-slate-400">
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatTimeAgo(release.deployed_at)}
                    </div>
                    {release.triggered_by && (
                      <div className="flex items-center text-slate-400">
                        <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        {release.triggered_by}
                      </div>
                    )}
                  </div>
                  <div className="pt-3 border-t border-slate-700/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-slate-400">Risk Score</span>
                      <span className="text-sm font-bold text-white">{release.risk_score.toFixed(0)}</span>
                    </div>
                    <div className="w-full bg-slate-800/60 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          release.risk_level === 'Healthy' ? 'bg-green-500' :
                          release.risk_level === 'Suspect' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${release.risk_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {releases.map((release) => (
                <div
                  key={release.id}
                  onClick={() => handleReleaseClick(release)}
                  className={`bg-slate-900/60 backdrop-blur-lg border rounded-xl p-6 cursor-pointer transition-all ${
                    selectedRelease?.id === release.id ? 'border-cyan-400 ring-1 ring-cyan-400/50' : 'border-slate-700 hover:border-cyan-400/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 flex-1">
                      <div>
                        <h3 className="text-lg font-bold text-white">v{release.version}</h3>
                        <p className="text-sm text-slate-500 font-mono">{truncate(release.commit, 8)}</p>
                      </div>
                      <div className="text-sm text-slate-400">{formatDateTime(release.deployed_at)}</div>
                      {release.triggered_by && (
                        <div className="text-sm text-slate-400">by {release.triggered_by}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm text-slate-400">Risk Score</p>
                        <p className="text-xl font-bold text-white">{release.risk_score.toFixed(0)}</p>
                      </div>
                      <RiskBadge level={release.risk_level} />
                      <Badge variant={release.status === 'success' ? 'success' : 'danger'}>
                        {release.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* CloudHelm Assistant */}
      <CloudHelmAssistant 
        repositoryId={selectedRepo || undefined}
        repositoryName={currentRepo?.name}
      />
    </div>
  );
}
