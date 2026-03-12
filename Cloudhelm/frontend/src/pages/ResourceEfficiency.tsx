import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { api } from '../lib/api';
import { LoadingSpinner } from '../components/resource-efficiency/LoadingState';

interface EfficiencyData {
  scatter_data: {
    service: string;
    cpu_pct: number;
    cost: number;
    efficiency: number;
  }[];
  recommendations: string[];
  avg_efficiency: number;
}

export default function ResourceEfficiency() {
  const [data, setData] = useState<EfficiencyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await api.getEfficiencyAnalysis();
      setData(result);
      setError(null);
    } catch (err: any) {
      console.error('Error loading efficiency data:', err);
      setError(err.message || 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: 'grafana' | 'gemini') => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(type);
      if (type === 'grafana') {
        await api.uploadGrafanaCsv(file);
      } else {
        await api.uploadGeminiCsv(file);
      }
      loadData();
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(null);
    }
  };

  const getEfficiencyColor = (score: number) => {
    if (score > 0.8) return '#10b981'; // green-500
    if (score > 0.5) return '#f59e0b'; // amber-500
    return '#ef4444'; // red-500
  };

  if (loading && !data) {
    return (
      <div className="p-6 min-h-screen bg-[#020204] flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="p-6 min-h-screen bg-[#020204]">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 italic tracking-tight">RESOURCE <span className="text-cyan-400">EFFICIENCY</span></h1>
            <p className="text-slate-400">Cost vs CPU Utilization Analysis (Linear Regression Model)</p>
          </div>
          <div className="flex gap-4">
            <div className="relative">
              <input
                type="file"
                id="grafana-upload"
                className="hidden"
                accept=".csv"
                onChange={(e) => handleFileUpload(e, 'grafana')}
                disabled={!!uploading}
              />
              <label
                htmlFor="grafana-upload"
                className={`px-4 py-2 rounded-lg text-sm font-bold border border-slate-700 cursor-pointer flex items-center gap-2 transition-all ${
                  uploading === 'grafana' ? 'bg-slate-800 text-slate-500' : 'bg-slate-900/50 text-slate-300 hover:bg-slate-800 hover:border-cyan-500/50'
                }`}
              >
                {uploading === 'grafana' ? 'Process...' : 'Upload Grafana CSV'}
              </label>
            </div>
            <div className="relative">
              <input
                type="file"
                id="gemini-upload"
                className="hidden"
                accept=".csv"
                onChange={(e) => handleFileUpload(e, 'gemini')}
                disabled={!!uploading}
              />
              <label
                htmlFor="gemini-upload"
                className={`px-4 py-2 rounded-lg text-sm font-bold border border-slate-700 cursor-pointer flex items-center gap-2 transition-all ${
                   uploading === 'gemini' ? 'bg-slate-800 text-slate-500' : 'bg-slate-900/50 text-slate-300 hover:bg-slate-800 hover:border-purple-500/50'
                }`}
              >
                {uploading === 'gemini' ? 'Process...' : 'Upload Gemini CSV'}
              </label>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full -mr-16 -mt-16 group-hover:scale-110 transition-transform" />
            <p className="text-sm text-slate-400 font-medium mb-1">Overall Efficiency Score</p>
            <div className="flex items-baseline gap-2">
              <h2 className="text-4xl font-bold text-white">{(data?.avg_efficiency || 0 * 100).toFixed(0)}%</h2>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                (data?.avg_efficiency || 0) > 0.7 ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {(data?.avg_efficiency || 0) > 0.7 ? 'OPTIMIZED' : 'NEEDS ATTENTION'}
              </span>
            </div>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
            <p className="text-sm text-slate-400 font-medium mb-1">Total Services Analyzed</p>
            <h2 className="text-4xl font-bold text-white">{data?.scatter_data.length || 0}</h2>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
            <p className="text-sm text-slate-400 font-medium mb-1">Optimization Opportunity</p>
            <h2 className="text-4xl font-bold text-emerald-400">{data?.recommendations.length || 0}</h2>
          </div>
        </div>

        {/* Chart and Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Scatter Plot */}
          <div className="lg:col-span-2 bg-slate-900/40 backdrop-blur-lg border border-slate-800/50 rounded-3xl p-8">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold text-white">Cost vs. Utilization Cluster</h3>
              <div className="flex gap-4 text-xs font-mono text-slate-500">
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-emerald-500"/> Healthy</div>
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-amber-500"/> Fair</div>
                <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-red-500"/> Wasteful</div>
              </div>
            </div>
            
            <div className="h-[400px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis 
                    type="number" 
                    dataKey="cpu_pct" 
                    name="CPU Utilization" 
                    unit="%" 
                    stroke="#64748b" 
                    fontSize={12}
                    label={{ value: 'utilization (%)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 10 }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="cost" 
                    name="Monthly Cost" 
                    unit="$" 
                    stroke="#64748b" 
                    fontSize={12}
                    label={{ value: 'monthly cost ($)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                  />
                  <ZAxis type="number" dataKey="efficiency" range={[100, 1000]} />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-[#0f172a] border border-slate-700 p-4 rounded-xl shadow-2xl backdrop-blur-xl">
                            <p className="text-white font-bold mb-2 border-b border-slate-800 pb-2">{data.service}</p>
                            <div className="space-y-1.5">
                              <div className="flex justify-between gap-8">
                                <span className="text-slate-400 text-xs">CPU Utilization</span>
                                <span className="text-white text-xs font-mono font-bold">{data.cpu_pct}%</span>
                              </div>
                              <div className="flex justify-between gap-8">
                                <span className="text-slate-400 text-xs">Monthly Cost</span>
                                <span className="text-white text-xs font-mono font-bold">${data.cost.toLocaleString()}</span>
                              </div>
                              <div className="flex justify-between gap-8 mt-2 pt-2 border-t border-slate-800">
                                <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Efficiency</span>
                                <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: `${getEfficiencyColor(data.efficiency)}20`, color: getEfficiencyColor(data.efficiency) }}>
                                  {Math.round(data.efficiency * 100)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter name="Services" data={data?.scatter_data || []}>
                    {data?.scatter_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getEfficiencyColor(entry.efficiency)} fillOpacity={0.6} stroke={getEfficiencyColor(entry.efficiency)} strokeWidth={2} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recommendations and Insights */}
          <div className="space-y-6">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Smart Recommendations
              </h3>
              <div className="space-y-4">
                {data?.recommendations.length ? data.recommendations.map((rec, i) => (
                  <div key={i} className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 flex gap-3 group hover:border-emerald-500/30 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                      <svg className="w-3.5 h-3.5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <p className="text-sm text-slate-300 group-hover:text-white transition-colors">{rec}</p>
                  </div>
                )) : (
                  <div className="text-center py-8">
                    <p className="text-slate-500 italic">No recommendations found. Upload more data for deep analysis.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-linear-to-br from-indigo-500/10 to-purple-500/10 backdrop-blur-md border border-indigo-500/20 rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-3">Model Insight</h3>
                <p className="text-sm text-slate-300 leading-relaxed mb-4">
                  Our system uses a <strong>Linear Regression cluster analysis</strong> to identify services deviating from the optimal utilization-to-cost ratio.
                </p>
                <div className="flex items-center gap-2 text-xs font-mono text-indigo-300 bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20">
                  <span>score = cpu_util / 50 * (1 / norm_cost)</span>
                </div>
            </div>
          </div>
        </div>

        {/* Details Table */}
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800">
            <h3 className="text-lg font-bold text-white">Efficiency Deep-Dive</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-800/30">
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Service</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">CPU Util (%)</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Monthly Cost ($)</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Efficiency</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data?.scatter_data.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4 text-white font-medium">{row.service}</td>
                    <td className="px-6 py-4 text-slate-300 font-mono">{row.cpu_pct}%</td>
                    <td className="px-6 py-4 text-slate-300 font-mono">${row.cost.toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${row.efficiency * 100}%`, backgroundColor: getEfficiencyColor(row.efficiency) }} />
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        row.efficiency > 0.8 ? 'bg-green-500/10 text-green-500' :
                        row.efficiency > 0.5 ? 'bg-amber-500/10 text-amber-500' : 'bg-red-500/10 text-red-500'
                      }`}>
                        {row.efficiency > 0.8 ? 'OPTIMAL' : row.efficiency > 0.5 ? 'FAIR' : 'WASTEFUL'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
