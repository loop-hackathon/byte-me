import { useState, useEffect } from 'react';
import { 
  TrendingUp, AlertTriangle, DollarSign, 
  Activity, Zap, Server, Users, ArrowUp, ArrowDown, Target
} from 'lucide-react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Area, AreaChart, ReferenceDot 
} from 'recharts';
import { api } from '../lib/api';
import type {
  KPISummary,
  CostTimeSeries,
  SpendByTeam,
  SpendByProvider,
  OptimizationOpportunities,
  ReliabilityMetrics,
  DeploymentStats
} from '../types/overview';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  trend?: Array<{ value: number }>;
}

function KPICard({ title, value, delta, deltaType, icon: Icon, trend }: KPICardProps) {
  const isPositive = deltaType === 'positive';
  const isNegative = deltaType === 'negative';
  
  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-5 hover:bg-slate-900/80 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all duration-300">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-400 mb-1.5">{title}</p>
          <p className="text-2xl font-bold text-slate-100">{value}</p>
        </div>
        <div className="w-10 h-10 bg-cyan-500/10 rounded-lg flex items-center justify-center flex-shrink-0 border border-cyan-500/20">
          <Icon className="w-5 h-5 text-cyan-400" />
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
      
      {trend && (
        <div className="mt-3 h-8">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend}>
              <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

const formatCurrency = (value: number): string => {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toLocaleString()}`;
};

export default function Overview() {
  const [timeRange, setTimeRange] = useState('30d');
  const [environment, setEnvironment] = useState('all');
  
  // State for all data sections
  const [kpiData, setKpiData] = useState<KPISummary | null>(null);
  const [costTimeSeriesData, setCostTimeSeriesData] = useState<CostTimeSeries | null>(null);
  const [spendByTeamData, setSpendByTeamData] = useState<SpendByTeam | null>(null);
  const [spendByProviderData, setSpendByProviderData] = useState<SpendByProvider | null>(null);
  const [optimizationData, setOptimizationData] = useState<OptimizationOpportunities | null>(null);
  const [reliabilityData, setReliabilityData] = useState<ReliabilityMetrics | null>(null);
  const [deploymentData, setDeploymentData] = useState<DeploymentStats | null>(null);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const [kpi, timeSeries, byTeam, byProvider, optimization, reliability, deployments] = 
          await Promise.all([
            api.getKPISummary({ time_range: timeRange, environment }),
            api.getCostTimeSeries({ time_range: timeRange, environment }),
            api.getSpendByTeam({ time_range: timeRange, environment, limit: 5 }),
            api.getSpendByProvider({ time_range: timeRange, environment }),
            api.getOptimizationOpportunities(4),
            api.getReliabilityMetrics(timeRange),
            api.getDeploymentStats()
          ]);
        
        setKpiData(kpi);
        setCostTimeSeriesData(timeSeries);
        setSpendByTeamData(byTeam);
        setSpendByProviderData(byProvider);
        setOptimizationData(optimization);
        setReliabilityData(reliability);
        setDeploymentData(deployments);
      } catch (err) {
        console.error('Failed to fetch overview data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, environment]);

  return (
    <div className="min-h-screen bg-[#020204] text-white">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-white">CloudHelm Executive Cockpit</h1>
            <p className="text-sm text-slate-400">Real-time visibility into cloud operations, costs, and reliability</p>
          </div>
          
          {/* Global Filters */}
          <div className="flex items-center gap-4">
            {/* Environment Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-400">Environment:</label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-slate-100"
              >
                <option value="all">All</option>
                <option value="prod">Production</option>
                <option value="staging">Staging</option>
                <option value="dev">Development</option>
              </select>
            </div>
            
            {/* Time Range Filter */}
            <div className="flex items-center gap-2 bg-slate-900/60 backdrop-blur-lg rounded-lg p-1 border border-slate-700">
              {['7d', '30d', '90d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-all ${
                    timeRange === range
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-slate-100 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                      : 'text-slate-400 hover:text-slate-100'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <div className="text-center">
              <div className="relative w-16 h-16 mx-auto mb-6">
                <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-cyan-400 rounded-full border-t-transparent animate-spin"></div>
                <div className="absolute inset-2 border-4 border-blue-500 rounded-full border-t-transparent animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1s' }}></div>
              </div>
              <p className="text-slate-400 font-medium">Loading overview data...</p>
              <div className="mt-2 flex items-center justify-center gap-1">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 backdrop-blur-lg border border-red-500/20 rounded-lg p-4">
            <p className="text-red-400">Error loading data: {error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 text-sm text-red-400 hover:text-red-300 underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* KPI Strip - Row 1: Cost Metrics */}
        {!loading && !error && kpiData && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              <KPICard
                title="Total Cloud Spend"
                value={formatCurrency(kpiData.total_cloud_spend)}
                delta={kpiData.deltas.spend_delta}
                deltaType={kpiData.deltas.spend_delta.startsWith('+') ? 'negative' : 'positive'}
                icon={DollarSign}
              />
              <KPICard
                title="Spend vs Budget"
                value={`${kpiData.spend_vs_budget.percentage.toFixed(1)}% ${kpiData.spend_vs_budget.status === 'over' ? 'Over' : kpiData.spend_vs_budget.status === 'under' ? 'Under' : 'At Risk'}`}
                delta={kpiData.deltas.spend_delta}
                deltaType={kpiData.spend_vs_budget.status === 'over' ? 'negative' : 'positive'}
                icon={Target}
              />
              <KPICard
                title="Forecasted Month-End"
                value={formatCurrency(kpiData.forecasted_month_end)}
                delta="+5.8%"
                deltaType="neutral"
                icon={TrendingUp}
              />
              <KPICard
                title="Active Anomalies"
                value={kpiData.active_anomalies.toString()}
                delta={kpiData.deltas.anomalies_delta}
                deltaType={kpiData.deltas.anomalies_delta.startsWith('-') ? 'positive' : 'negative'}
                icon={AlertTriangle}
              />
              <KPICard
                title="Potential Savings"
                value={`${formatCurrency(kpiData.potential_savings)}/mo`}
                delta="+$4.2K"
                deltaType="positive"
                icon={Zap}
              />
            </div>

            {/* KPI Strip - Row 2: Reliability & Operations Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <KPICard
                title="Open Incidents"
                value={kpiData.open_incidents.toString()}
                delta={kpiData.deltas.incidents_delta}
                deltaType={kpiData.deltas.incidents_delta.startsWith('-') ? 'positive' : 'negative'}
                icon={AlertTriangle}
              />
              <KPICard
                title="Availability"
                value={`${kpiData.availability.toFixed(2)}%`}
                delta="+0.02%"
                deltaType="positive"
                icon={Activity}
              />
              <KPICard
                title="Deployments (7d)"
                value={kpiData.deployments_count.toString()}
                delta={kpiData.deltas.deployments_delta}
                deltaType="positive"
                icon={Server}
              />
              <KPICard
                title="Teams at Risk"
                value={kpiData.teams_at_risk.toString()}
                delta="-1"
                deltaType="positive"
                icon={Users}
              />
            </div>
          </>
        )}

        {/* Main Cost Visualization */}
        {!loading && !error && costTimeSeriesData && (
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-slate-100">Cost Over Time</h2>
              <p className="text-sm text-slate-400 mt-1">Daily spend with forecast and anomaly detection</p>
            </div>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={costTimeSeriesData.series}>
                  <defs>
                    <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9ca3af" 
                    style={{ fontSize: '12px' }}
                    tick={{ fill: '#9ca3af' }}
                  />
                  <YAxis 
                    stroke="#9ca3af" 
                    style={{ fontSize: '12px' }} 
                    tickFormatter={(value) => `$${value/1000}K`}
                    tick={{ fill: '#9ca3af' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(3, 5, 8, 0.95)', 
                      border: '1px solid rgba(255,255,255,0.1)', 
                      borderRadius: '8px',
                      backdropFilter: 'blur(10px)',
                      color: '#fff'
                    }}
                    formatter={(value: any) => [`$${value.toLocaleString()}`, '']}
                    labelStyle={{ fontWeight: 600, marginBottom: '4px', color: '#22d3ee' }}
                  />
                  <Legend 
                    wrapperStyle={{ paddingTop: '20px' }}
                    iconType="line"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="cost" 
                    stroke="#22d3ee" 
                    strokeWidth={2} 
                    fill="url(#colorCost)" 
                    name="Actual Cost" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="forecast" 
                    stroke="#10b981" 
                    strokeWidth={2} 
                    strokeDasharray="5 5" 
                    dot={false} 
                    name="Forecast" 
                  />
                  {costTimeSeriesData.series.map((entry, index) => 
                    entry.anomaly ? (
                      <ReferenceDot
                        key={`anomaly-${index}`}
                        x={entry.date}
                        y={entry.cost}
                        r={6}
                        fill="#ef4444"
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    ) : null
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Breakdown Visualizations */}
        {!loading && !error && spendByTeamData && spendByProviderData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Spend by Team */}
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-100">Spend by Team</h2>
                <p className="text-sm text-slate-400 mt-1">Top spending teams this period</p>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={spendByTeamData.breakdown} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      type="number" 
                      stroke="#9ca3af" 
                      style={{ fontSize: '12px' }} 
                      tickFormatter={(value) => `$${value/1000}K`}
                      tick={{ fill: '#9ca3af' }}
                    />
                    <YAxis 
                      type="category" 
                      dataKey="team" 
                      stroke="#9ca3af" 
                      style={{ fontSize: '12px' }} 
                      width={110}
                      tick={{ fill: '#9ca3af' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(3, 5, 8, 0.95)', 
                        border: '1px solid rgba(255,255,255,0.1)', 
                        borderRadius: '8px',
                        backdropFilter: 'blur(10px)',
                        color: '#fff'
                      }}
                      formatter={(value: any) => [`$${value.toLocaleString()}`, 'Spend']}
                      cursor={{ fill: 'rgba(34, 211, 238, 0.1)' }}
                    />
                    <Bar dataKey="spend" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Spend by Provider */}
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-100">Spend by Cloud Provider</h2>
                <p className="text-sm text-slate-400 mt-1">Distribution across AWS, Azure, and GCP</p>
              </div>
              <div className="h-72 flex items-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={spendByProviderData.breakdown}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="percentage"
                    >
                      {spendByProviderData.breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(3, 5, 8, 0.95)', 
                        border: '1px solid rgba(255,255,255,0.1)', 
                        borderRadius: '8px',
                        backdropFilter: 'blur(10px)',
                        color: '#fff'
                      }}
                      formatter={(value: any, name: any, props: any) => [
                        `${value}% ($${props.payload.spend.toLocaleString()})`, 
                        props.payload.provider
                      ]}
                    />
                    <Legend 
                      verticalAlign="middle" 
                      align="right"
                      layout="vertical"
                      formatter={(value, entry: any) => (
                        <span className="text-sm text-slate-400">
                          <span className="font-semibold">{entry.payload.provider}</span>
                          <span className="text-slate-500"> {entry.payload.percentage}%</span>
                        </span>
                      )}
                      iconType="circle"
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Anomalies & Opportunities */}
        {!loading && !error && optimizationData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Cost Anomalies */}
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100">Top Cost Anomalies</h2>
                  <p className="text-sm text-slate-400 mt-1">Unusual spending patterns detected</p>
                </div>
                <button className="text-sm text-cyan-400 hover:text-cyan-300 font-semibold hover:underline">
                  View All
                </button>
              </div>
              
              <div className="space-y-3">
                {kpiData && kpiData.active_anomalies === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <p>No anomalies detected</p>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <p>Anomaly details available in Cost Dashboard</p>
                  </div>
                )}
              </div>
            </div>

            {/* Top Optimization Opportunities */}
            <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100">Optimization Opportunities</h2>
                  <p className="text-sm text-slate-400 mt-1">Potential cost savings identified</p>
                </div>
                <button className="text-sm text-cyan-400 hover:text-cyan-300 font-semibold hover:underline">
                  View All
                </button>
              </div>
              
              <div className="space-y-3">
                {optimizationData.opportunities.map((opp, index) => (
                  <div 
                    key={index} 
                    className="p-3 bg-slate-800/40 rounded-lg hover:bg-slate-800/60 transition-colors cursor-pointer border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <p className="text-sm font-semibold text-slate-100 flex-1">{opp.resource}</p>
                      <span className="text-sm font-bold text-green-400">
                        {formatCurrency(opp.estimated_savings)}/mo
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-medium border border-purple-500/30">
                        {opp.type}
                      </span>
                      <span className="text-xs text-slate-400">{opp.recommended_action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Reliability & Releases Snapshot */}
        {!loading && !error && reliabilityData && deploymentData && (
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-slate-100">Reliability & Releases</h2>
              <p className="text-sm text-slate-400 mt-1">System health and deployment activity</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Open Incidents */}
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-3">Open Incidents</h3>
                <div className="space-y-2">
                  {reliabilityData.open_incidents.length === 0 ? (
                    <div className="p-3 bg-green-500/10 rounded-lg text-center border border-green-500/20">
                      <p className="text-sm text-green-400">No open incidents</p>
                    </div>
                  ) : (
                    reliabilityData.open_incidents.slice(0, 2).map((incident) => (
                      <div key={incident.id} className="p-3 bg-slate-800/40 rounded-lg hover:bg-slate-800/60 transition-colors cursor-pointer border border-slate-700/50">
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-sm font-semibold text-slate-100 flex-1">{incident.title}</p>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${
                            incident.severity === 'high' ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                          }`}>
                            {incident.severity}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded font-medium border border-blue-500/30">
                            {incident.status}
                          </span>
                          <span className="text-slate-400">{incident.duration}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Availability Metrics */}
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-3">Availability Metrics</h3>
                <div className="space-y-3">
                  <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                    <p className="text-xs font-medium text-slate-400 mb-1">Uptime ({timeRange})</p>
                    <p className="text-2xl font-bold text-green-400">{reliabilityData.availability.percentage.toFixed(2)}%</p>
                    <div className="flex items-center gap-1 mt-2">
                      <ArrowUp className="w-3 h-3 text-green-400" />
                      <p className="text-xs font-semibold text-green-400">{reliabilityData.availability.delta} vs last period</p>
                    </div>
                  </div>
                  <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <p className="text-xs font-medium text-slate-400 mb-1">Error Rate</p>
                    <p className="text-2xl font-bold text-blue-400">{reliabilityData.error_rate.percentage.toFixed(2)}%</p>
                    <div className="flex items-center gap-1 mt-2">
                      <ArrowDown className="w-3 h-3 text-green-400" />
                      <p className="text-xs font-semibold text-green-400">{reliabilityData.error_rate.delta} vs last period</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Deployments */}
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-3">Recent Deployments (7d)</h3>
                <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 mb-3">
                  <p className="text-3xl font-bold text-slate-100 mb-1">{deploymentData.total_deployments}</p>
                  <p className="text-xs font-medium text-slate-400">Total deployments</p>
                  <div className="flex items-center gap-1 mt-2">
                    <ArrowUp className="w-3 h-3 text-green-400" />
                    <span className="text-sm font-semibold text-green-400">{deploymentData.delta} vs last week</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20 text-center">
                    <p className="text-xl font-bold text-green-400">{deploymentData.successful}</p>
                    <p className="text-xs font-medium text-slate-400 mt-1">Successful</p>
                  </div>
                  <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20 text-center">
                    <p className="text-xl font-bold text-red-400">{deploymentData.failed}</p>
                    <p className="text-xs font-medium text-slate-400 mt-1">Failed</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
