import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import CostSummaryCards from '../components/Cost/CostSummaryCards';
import CostTimeSeriesChart from '../components/Cost/CostTimeSeriesChart';
import CostAnomaliesTable from '../components/Cost/CostAnomaliesTable';
import BudgetStatusTable from '../components/Cost/BudgetStatusTable';
import type { CostSummaryResponse, CostAnomaly, BudgetStatus } from '../types/cost';

export default function CostDashboard() {
  const [timeRange, setTimeRange] = useState('30d');
  const [groupBy, setGroupBy] = useState('team');
  const [env, setEnv] = useState('all');
  
  const [costData, setCostData] = useState<CostSummaryResponse | null>(null);
  const [anomalies, setAnomalies] = useState<CostAnomaly[]>([]);
  const [budgets, setBudgets] = useState<BudgetStatus[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadData();
  }, [timeRange, groupBy, env]);

  const getDateRange = () => {
    const today = new Date();
    const from = new Date(today);
    
    switch (timeRange) {
      case '7d':
        from.setDate(today.getDate() - 7);
        break;
      case '30d':
        from.setDate(today.getDate() - 30);
        break;
      case '90d':
        from.setDate(today.getDate() - 90);
        break;
      default:
        from.setDate(today.getDate() - 30);
    }
    
    return {
      from: from.toISOString().split('T')[0],
      to: today.toISOString().split('T')[0]
    };
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const { from, to } = getDateRange();
      
      const params: any = { from, to, group_by: groupBy };
      if (env !== 'all') {
        params.env = env;
      }

      const [costResponse, anomaliesResponse, budgetsResponse] = await Promise.all([
        api.getCostSummary(params),
        api.getCostAnomalies({ from, to }),
        api.getBudgetStatus()
      ]);

      setCostData(costResponse);
      setAnomalies(anomaliesResponse);
      setBudgets(budgetsResponse);
    } catch (error) {
      console.error('Error loading cost data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (provider: 'aws' | 'gcp' | 'azure', event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploadingFile(true);
      setUploadMessage(null);
      
      const response = await api.uploadCostFile(provider, file);
      
      setUploadMessage({
        type: 'success',
        text: `Successfully uploaded ${response.rows_ingested} rows (${response.start_date} to ${response.end_date}). Total: $${response.total_cost.toFixed(2)}`
      });

      // Trigger recompute
      await api.recomputeAggregates();
      await api.recomputeAnomalies();
      
      // Reload data
      await loadData();
    } catch (error: any) {
      setUploadMessage({
        type: 'error',
        text: error.message || 'Failed to upload file'
      });
    } finally {
      setUploadingFile(false);
      event.target.value = '';
    }
  };

  return (
    <div className="p-6 min-h-screen bg-[#020204]">
      <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Cost Dashboard</h1>
        <p className="text-slate-400 mt-1">Monitor and analyze cloud spending</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Time Range
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 text-slate-100"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Group By
            </label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 text-slate-100"
            >
              <option value="team">Team</option>
              <option value="service">Service</option>
              <option value="cloud">Cloud Provider</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Environment
            </label>
            <select
              value={env}
              onChange={(e) => setEnv(e.target.value)}
              className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 text-slate-100"
            >
              <option value="all">All</option>
              <option value="prod">Production</option>
              <option value="stage">Staging</option>
              <option value="dev">Development</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-32">
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-6">
              {/* Glassmorphism Container */}
              <div className="absolute inset-0 bg-white/5 rounded-full backdrop-blur-xl border border-white/10 shadow-2xl"></div>
              <div className="absolute inset-2 bg-white/3 rounded-full backdrop-blur-lg"></div>
              
              {/* Rotating Rings */}
              <div className="absolute inset-0 border-4 border-transparent border-t-white/40 rounded-full animate-spin"></div>
              <div className="absolute inset-3 border-4 border-transparent border-t-white/30 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
              <div className="absolute inset-6 border-4 border-transparent border-t-white/20 rounded-full animate-spin" style={{ animationDuration: '2s' }}></div>
              
              {/* Center Glow */}
              <div className="absolute inset-8 bg-white/10 rounded-full blur-md animate-pulse"></div>
            </div>
            <p className="text-slate-300 font-medium text-lg mb-2">Loading cost data...</p>
            <div className="flex items-center justify-center gap-1.5">
              <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {!loading && (
        <CostSummaryCards
          costData={costData}
          budgets={budgets}
          anomalyCount={anomalies.length}
          loading={loading}
        />
      )}

      {/* File Upload Section */}
      <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">Upload Cost Exports</h3>
        
        {uploadMessage && (
          <div className={`mb-4 p-4 rounded-lg ${
            uploadMessage.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {uploadMessage.text}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              AWS Cost & Usage Report
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => handleFileUpload('aws', e)}
              disabled={uploadingFile}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              GCP Billing Export
            </label>
            <input
              type="file"
              accept=".csv,.json"
              onChange={(e) => handleFileUpload('gcp', e)}
              disabled={uploadingFile}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Azure Cost Export
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => handleFileUpload('azure', e)}
              disabled={uploadingFile}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20 disabled:opacity-50"
            />
          </div>
        </div>

        {uploadingFile && (
          <div className="mt-4 flex items-center gap-3 text-sm text-slate-300">
            <div className="relative w-5 h-5">
              <div className="absolute inset-0 border-2 border-transparent border-t-white/40 rounded-full animate-spin"></div>
              <div className="absolute inset-0.5 border-2 border-transparent border-t-white/30 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1s' }}></div>
            </div>
            <span className="font-medium">Uploading and processing file...</span>
          </div>
        )}
      </div>

      {/* Cost Chart */}
      <CostTimeSeriesChart
        costData={costData}
        anomalies={anomalies}
        loading={loading}
      />

      {/* Anomalies Table */}
      <CostAnomaliesTable
        anomalies={anomalies}
        loading={loading}
      />

      {/* Budget Status Table */}
      <BudgetStatusTable
        budgets={budgets}
        loading={loading}
      />
      </div>
    </div>
  );
}
