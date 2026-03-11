import { useState, useEffect } from 'react';
import { 
  Activity, AlertTriangle, CheckCircle2, XCircle, RefreshCw,
  Server, Container, Cloud, TrendingUp, Zap, Database,
  Cpu, HardDrive, Network, ArrowUp, ArrowDown
} from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar
} from 'recharts';
import { api } from '../lib/api';
import type { 
  ServiceHealth, Anomaly, MetricHistory,
  Container as DockerContainer, Pod, ClusterHealth,
  InfrastructureAvailability
} from '../types/health';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  color?: string;
}

function KPICard({ title, value, delta, deltaType, icon: Icon, color = 'cyan' }: KPICardProps) {
  const isPositive = deltaType === 'positive';
  const isNegative = deltaType === 'negative';
  
  const colorClasses = {
    cyan: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    green: 'bg-green-500/10 border-green-500/20 text-green-400',
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  }[color] || 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400';
  
  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-5 hover:bg-slate-900/80 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all duration-300">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-400 mb-1.5">{title}</p>
          <p className="text-2xl font-bold text-slate-100">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border ${colorClasses}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      
      {delta && (
        <div className="flex items-center gap-1.5">
          {isPositive && <ArrowUp className="w-3.5 h-3.5 text-green-400" />}
          {isNegative && <ArrowDown className="w-3.5 h-3.5 text-red-400" />}
          <span className={`text-xs font-semibold ${isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-slate-400'}`}>
            {delta}
          </span>
          <span className="text-xs text-slate-500">vs last period</span>
        </div>
      )}
    </div>
  );
}

export default function AppHealth() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [infrastructure, setInfrastructure] = useState<InfrastructureAvailability | null>(null);
  const [containers, setContainers] = useState<DockerContainer[]>([]);
  const [pods, setPods] = useState<Pod[]>([]);
  const [clusterHealth, setClusterHealth] = useState<ClusterHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<MetricHistory[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [activeTab, setActiveTab] = useState<'services' | 'anomalies' | 'infrastructure'>('services');

  useEffect(() => {
    loadAllData();
    if (autoRefresh) {
      const interval = setInterval(loadAllData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  useEffect(() => {
    if (selectedService) {
      loadMetricsHistory(selectedService);
    }
  }, [selectedService]);

  const loadAllData = async () => {
    try {
      setRefreshing(true);
      const [healthData, anomalyData, infraData] = await Promise.all([
        api.getHealthSummary(),
        api.getAnomalies({ hours: 24 }),
        api.getInfrastructureAvailability()
      ]);

      setServices(healthData);
      setAnomalies(anomalyData);
      setInfrastructure(infraData);

      if (infraData.docker_available) {
        const dockerContainers = await api.getDockerContainers();
        setContainers(dockerContainers);
      }

      if (infraData.kubernetes_available) {
        const [k8sPods, k8sHealth] = await Promise.all([
          api.getKubernetesPods(),
          api.getClusterHealth()
        ]);
        setPods(k8sPods);
        setClusterHealth(k8sHealth);
      }

      if (healthData.length > 0 && !selectedService) {
        setSelectedService(healthData[0].service_name);
      }
    } catch (error) {
      console.error('Failed to load health data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadMetricsHistory = async (serviceName: string) => {
    try {
      const history = await api.getMetricsHistory(serviceName, 6);
      setMetricsHistory(history);
    } catch (error) {
      console.error('Failed to load metrics history:', error);
    }
  };

  const handleSeedData = async () => {
    try {
      setSeeding(true);
      await api.seedHealthData(24);
      await loadAllData();
      alert('Demo data seeded successfully!');
    } catch (error) {
      console.error('Failed to seed data:', error);
      alert('Failed to seed data. Check console for details.');
    } finally {
      setSeeding(false);
    }
  };

  const getOverallHealth = () => {
    if (services.length === 0) return { score: 0, status: 'unknown' };
    const avgScore = services.reduce((sum, s) => sum + s.health_score, 0) / services.length;
    const status = avgScore >= 90 ? 'healthy' : avgScore >= 70 ? 'degraded' : avgScore >= 50 ? 'warning' : 'critical';
    return { score: Math.round(avgScore), status };
  };

  const getCriticalAnomalies = () => anomalies.filter(a => a.severity === 'critical').length;
  const getHealthyServices = () => services.filter(s => s.status === 'healthy').length;

  const formatLatency = (ms: number) => ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(2)}s`;
  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)}GB`;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <RefreshCw className="w-12 h-12 animate-spin text-cyan-400" />
        <p className="text-slate-400">Loading health monitoring data...</p>
      </div>
    );
  }

  const overallHealth = getOverallHealth();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-2">App Health</h1>
          <p className="text-slate-400">Real-time service monitoring with anomaly detection</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="px-4 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:border-cyan-500/50 transition-all"
          >
            <Zap className={`w-4 h-4 inline mr-2 ${autoRefresh ? 'text-cyan-400' : 'text-slate-500'}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={handleSeedData}
            disabled={seeding}
            className="px-4 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:border-cyan-500/50 transition-all disabled:opacity-50"
          >
            <Database className={`w-4 h-4 inline mr-2 ${seeding ? 'animate-pulse' : ''}`} />
            {seeding ? 'Seeding...' : 'Seed Demo Data'}
          </button>
          <button
            onClick={() => loadAllData()}
            disabled={refreshing}
            className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-sm text-cyan-400 hover:bg-cyan-500/20 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 inline mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Overall Health Score"
          value={overallHealth.score}
          icon={Activity}
          color="cyan"
        />
        <KPICard
          title="Healthy Services"
          value={getHealthyServices()}
          delta={`${services.length} total`}
          icon={CheckCircle2}
          color="green"
        />
        <KPICard
          title="Critical Anomalies"
          value={getCriticalAnomalies()}
          delta={`${anomalies.length} total`}
          deltaType={getCriticalAnomalies() > 0 ? 'negative' : 'positive'}
          icon={AlertTriangle}
          color="red"
        />
        <KPICard
          title="Infrastructure"
          value={`${(infrastructure?.docker_available ? 1 : 0) + (infrastructure?.kubernetes_available ? 1 : 0)}/2`}
          delta="Connected"
          icon={Server}
          color="purple"
        />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('services')}
          className={`px-4 py-2 text-sm font-medium transition-all ${
            activeTab === 'services'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Services
        </button>
        <button
          onClick={() => setActiveTab('anomalies')}
          className={`px-4 py-2 text-sm font-medium transition-all ${
            activeTab === 'anomalies'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          <AlertTriangle className="w-4 h-4 inline mr-2" />
          Anomalies ({anomalies.length})
        </button>
        <button
          onClick={() => setActiveTab('infrastructure')}
          className={`px-4 py-2 text-sm font-medium transition-all ${
            activeTab === 'infrastructure'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          <Server className="w-4 h-4 inline mr-2" />
          Infrastructure
        </button>
      </div>

      {/* Services Tab */}
      {activeTab === 'services' && (
        <div className="space-y-6">
          {services.length === 0 ? (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
              <Activity className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-300 mb-2">No Services Registered</h3>
              <p className="text-slate-400 mb-4">Click "Seed Demo Data" to generate sample services</p>
              <button
                onClick={handleSeedData}
                disabled={seeding}
                className="px-6 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 transition-all"
              >
                <Database className="w-4 h-4 inline mr-2" />
                Seed Demo Data
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {services.map((service) => (
                  <ServiceCard
                    key={service.service_name}
                    service={service}
                    isSelected={selectedService === service.service_name}
                    onClick={() => setSelectedService(service.service_name)}
                    formatLatency={formatLatency}
                    formatBytes={formatBytes}
                  />
                ))}
              </div>

              {selectedService && metricsHistory.length > 0 && (
                <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-cyan-400" />
                      Metrics History - {selectedService}
                    </h3>
                    <span className="text-xs text-slate-500">Last 6 hours</span>
                  </div>
                  <MetricsCharts history={metricsHistory} />
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Anomalies Tab */}
      {activeTab === 'anomalies' && (
        <div className="space-y-4">
          {anomalies.length === 0 ? (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
              <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-300 mb-2">No Anomalies Detected</h3>
              <p className="text-slate-400">All services are operating within normal parameters</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-400 mb-1">Total</p>
                  <p className="text-3xl font-bold text-slate-100">{anomalies.length}</p>
                </div>
                <div className="bg-slate-900/60 backdrop-blur-lg border border-red-500/30 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-400 mb-1">Critical</p>
                  <p className="text-3xl font-bold text-red-400">{getCriticalAnomalies()}</p>
                </div>
                <div className="bg-slate-900/60 backdrop-blur-lg border border-yellow-500/30 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-400 mb-1">High</p>
                  <p className="text-3xl font-bold text-yellow-400">
                    {anomalies.filter(a => a.severity === 'high').length}
                  </p>
                </div>
                <div className="bg-slate-900/60 backdrop-blur-lg border border-blue-500/30 rounded-xl p-4 text-center">
                  <p className="text-xs text-slate-400 mb-1">Medium/Low</p>
                  <p className="text-3xl font-bold text-blue-400">
                    {anomalies.filter(a => a.severity === 'medium' || a.severity === 'low').length}
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {anomalies.map((anomaly) => (
                  <AnomalyCard key={anomaly.id} anomaly={anomaly} />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Infrastructure Tab */}
      {activeTab === 'infrastructure' && (
        <div className="space-y-6">
          {infrastructure?.docker_available && (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                <Container className="w-5 h-5 text-green-400" />
                Docker Containers ({containers.length})
              </h3>
              {containers.length === 0 ? (
                <p className="text-center text-slate-400 py-8">No containers found</p>
              ) : (
                <DockerTable containers={containers} formatBytes={formatBytes} />
              )}
            </div>
          )}

          {infrastructure?.kubernetes_available && clusterHealth && (
            <>
              <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                  <Cloud className="w-5 h-5 text-blue-400" />
                  Cluster Health
                </h3>
                <ClusterHealthView health={clusterHealth} />
              </div>

              <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                  <Server className="w-5 h-5 text-blue-400" />
                  Kubernetes Pods ({pods.length})
                </h3>
                {pods.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">No pods found</p>
                ) : (
                  <PodsTable pods={pods} />
                )}
              </div>
            </>
          )}

          {!infrastructure?.docker_available && !infrastructure?.kubernetes_available && (
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-12 text-center">
              <Server className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-300 mb-2">No Infrastructure Connected</h3>
              <p className="text-slate-400">Connect Docker or Kubernetes to monitor infrastructure</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Service Card Component
function ServiceCard({ service, isSelected, onClick, formatLatency, formatBytes }: any) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'border-green-500/30 bg-green-500/5';
      case 'degraded': return 'border-yellow-500/30 bg-yellow-500/5';
      case 'warning': return 'border-orange-500/30 bg-orange-500/5';
      case 'critical': return 'border-red-500/30 bg-red-500/5';
      default: return 'border-slate-700';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      healthy: 'bg-green-500/10 text-green-400 border-green-500/30',
      degraded: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      warning: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      critical: 'bg-red-500/10 text-red-400 border-red-500/30',
    }[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/30';

    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold border ${colors} uppercase`}>
        {status}
      </span>
    );
  };

  const healthColor = service.health_score >= 90 ? '#10b981' : 
                      service.health_score >= 70 ? '#f59e0b' : 
                      service.health_score >= 50 ? '#f97316' : '#ef4444';

  return (
    <div
      onClick={onClick}
      className={`bg-slate-900/60 backdrop-blur-lg border rounded-xl p-5 cursor-pointer transition-all duration-300 hover:bg-slate-900/80 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] ${
        isSelected ? 'border-cyan-500 shadow-[0_0_20px_rgba(34,211,238,0.3)]' : getStatusColor(service.status)
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base font-semibold text-slate-100">{service.service_name}</h4>
        {getStatusBadge(service.status)}
      </div>

      <div className="flex items-center gap-4 mb-4">
        {/* Health Score Ring */}
        <div className="relative w-20 h-20 flex-shrink-0">
          <svg className="w-20 h-20 transform -rotate-90">
            <circle
              cx="40"
              cy="40"
              r="32"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="40"
              cy="40"
              r="32"
              stroke={healthColor}
              strokeWidth="6"
              fill="none"
              strokeDasharray={`${(service.health_score / 100) * 201} 201`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold text-slate-100">{Math.round(service.health_score)}</span>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-2 flex-1">
          <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">Req/s</p>
            <p className="text-sm font-bold text-slate-200">{service.request_rate.toFixed(1)}</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">Error %</p>
            <p className="text-sm font-bold text-red-400">{(service.error_rate * 100).toFixed(2)}%</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">P95</p>
            <p className="text-sm font-bold text-yellow-400">{formatLatency(service.latency.p95)}</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">CPU</p>
            <p className="text-sm font-bold text-purple-400">{(service.resources.cpu * 100).toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-700/50">
        <span className="flex items-center gap-1">
          <Server className="w-3 h-3" />
          {service.pod_count} pods
        </span>
        <span className="flex items-center gap-1">
          <RefreshCw className="w-3 h-3" />
          {service.restart_count} restarts
        </span>
        <span className="flex items-center gap-1">
          <HardDrive className="w-3 h-3" />
          {formatBytes(service.resources.memory)}
        </span>
      </div>
    </div>
  );
}

// Metrics Charts Component
function MetricsCharts({ history }: { history: MetricHistory[] }) {
  const chartData = history.map(h => ({
    time: new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    requestRate: h.request_rate,
    errorRate: h.error_rate * 100,
    latencyP50: h.latency_p50,
    latencyP95: h.latency_p95,
    latencyP99: h.latency_p99,
    cpu: h.cpu_usage * 100,
    memory: h.memory_usage / (1024 * 1024 * 1024),
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Request & Error Rates */}
      <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Request & Error Rates</h4>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorRequest" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorError" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
            <YAxis stroke="#64748b" fontSize={10} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Area type="monotone" dataKey="requestRate" stroke="#22d3ee" fill="url(#colorRequest)" strokeWidth={2} name="Req/s" />
            <Area type="monotone" dataKey="errorRate" stroke="#ef4444" fill="url(#colorError)" strokeWidth={2} name="Error %" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Latency Percentiles */}
      <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Latency Percentiles</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
            <YAxis stroke="#64748b" fontSize={10} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Line type="monotone" dataKey="latencyP50" stroke="#10b981" strokeWidth={2} name="P50" dot={{ r: 2 }} />
            <Line type="monotone" dataKey="latencyP95" stroke="#f59e0b" strokeWidth={2} name="P95" dot={{ r: 2 }} />
            <Line type="monotone" dataKey="latencyP99" stroke="#ef4444" strokeWidth={2} name="P99" dot={{ r: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Resource Usage */}
      <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Resource Usage</h4>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
            <YAxis stroke="#64748b" fontSize={10} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Area type="monotone" dataKey="cpu" stroke="#8b5cf6" fill="url(#colorCpu)" strokeWidth={2} name="CPU %" />
            <Area type="monotone" dataKey="memory" stroke="#06b6d4" fill="url(#colorMemory)" strokeWidth={2} name="Memory GB" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Pod Metrics */}
      <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Pod Metrics</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
            <YAxis stroke="#64748b" fontSize={10} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="pods" fill="#3b82f6" name="Pods" radius={[4, 4, 0, 0]} />
            <Bar dataKey="restarts" fill="#f97316" name="Restarts" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Anomaly Card Component
function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500/30 bg-red-500/5';
      case 'high': return 'border-yellow-500/30 bg-yellow-500/5';
      case 'medium': return 'border-blue-500/30 bg-blue-500/5';
      case 'low': return 'border-slate-500/30 bg-slate-500/5';
      default: return 'border-slate-700';
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      critical: 'bg-red-500/10 text-red-400 border-red-500/30',
      high: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      medium: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      low: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    }[severity] || 'bg-slate-500/10 text-slate-400 border-slate-500/30';

    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold border ${colors} uppercase`}>
        {severity}
      </span>
    );
  };

  return (
    <div className={`bg-slate-900/60 backdrop-blur-lg border rounded-xl p-5 ${getSeverityColor(anomaly.severity)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <div>
            <h4 className="text-base font-semibold text-slate-100">{anomaly.service_name}</h4>
            <p className="text-xs text-slate-500">Score: {anomaly.anomaly_score.toFixed(3)}</p>
          </div>
        </div>
        {getSeverityBadge(anomaly.severity)}
      </div>
      <p className="text-sm text-slate-300 mb-3">{anomaly.description}</p>
      <div className="flex flex-wrap gap-2 mb-3">
        {anomaly.affected_metrics.map((metric: string) => (
          <span key={metric} className="px-2 py-1 bg-purple-500/10 border border-purple-500/30 rounded text-xs text-purple-400">
            {metric}
          </span>
        ))}
      </div>
      <p className="text-xs text-slate-500">{new Date(anomaly.timestamp).toLocaleString()}</p>
    </div>
  );
}

// Docker Table Component
function DockerTable({ containers, formatBytes }: any) {
  return (
    <div className="space-y-2">
      {containers.map((container: DockerContainer) => (
        <div key={container.id} className="flex items-center justify-between p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${container.status === 'running' ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`} />
            <div>
              <p className="text-sm font-semibold text-slate-200">{container.name}</p>
              <p className="text-xs text-slate-500">{container.image}</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className={container.status === 'running' ? 'text-green-400' : ''}>{container.status}</span>
            {container.stats && (
              <>
                <span className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  {container.stats.cpu_percent.toFixed(1)}%
                </span>
                <span className="flex items-center gap-1">
                  <HardDrive className="w-3 h-3" />
                  {formatBytes(container.stats.memory_usage_bytes)}
                </span>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// Cluster Health View Component
function ClusterHealthView({ health }: { health: ClusterHealth }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-slate-800/40 rounded-lg p-4 border border-blue-500/30">
        <div className="flex items-center gap-2 mb-2">
          <Server className="w-4 h-4 text-blue-400" />
          <p className="text-xs text-slate-400">Nodes</p>
        </div>
        <p className="text-3xl font-bold text-slate-100">{health.nodes.ready}/{health.nodes.total}</p>
        <p className="text-xs text-slate-500 mt-1">Ready</p>
      </div>
      <div className="bg-slate-800/40 rounded-lg p-4 border border-green-500/30">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          <p className="text-xs text-slate-400">Pods</p>
        </div>
        <p className="text-3xl font-bold text-slate-100">{health.pods.running}/{health.pods.total}</p>
        <p className="text-xs text-slate-500 mt-1">Running</p>
      </div>
      <div className="bg-slate-800/40 rounded-lg p-4 border border-yellow-500/30">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <p className="text-xs text-slate-400">Issues</p>
        </div>
        <p className="text-3xl font-bold text-slate-100">{health.pods.pending + health.pods.failed}</p>
        <p className="text-xs text-slate-500 mt-1">Pending/Failed</p>
      </div>
    </div>
  );
}

// Pods Table Component
function PodsTable({ pods }: { pods: Pod[] }) {
  return (
    <div className="space-y-2">
      {pods.map((pod) => {
        const readyContainers = pod.container_statuses.filter(c => c.ready).length;
        const totalContainers = pod.container_statuses.length;
        
        return (
          <div key={pod.uid} className="flex items-center justify-between p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${pod.phase === 'Running' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`} />
              <div>
                <p className="text-sm font-semibold text-slate-200">{pod.name}</p>
                <p className="text-xs text-slate-500">{pod.namespace} • {pod.node_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className={pod.phase === 'Running' ? 'text-green-400' : 'text-yellow-400'}>{pod.phase}</span>
              <span>{readyContainers}/{totalContainers} ready</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
