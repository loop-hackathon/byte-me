import React, { useState } from 'react';
import { api } from '../lib/api';
import CostSummaryCards from '../components/Cost/CostSummaryCards';
import CostTimeSeriesChart from '../components/Cost/CostTimeSeriesChart';
import CostAnomaliesTable from '../components/Cost/CostAnomaliesTable';
import BudgetStatusTable from '../components/Cost/BudgetStatusTable';
import type { CostSummaryResponse, CostAnomaly, BudgetStatus } from '../types/cost';
import { generateSLAPDF } from '../lib/pdfExport';
import { Download } from 'lucide-react';

// ─── Types from the billing analysis response ───────────────────────────────

interface CostTrend {
  date: string;
  amount: number;
  service: string;
}

interface BillingAnomaly {
  date: string;
  service: string;
  amount: number;
  expected_amount: number;
  anomaly_type: string;
  severity: string;
  description?: string;
}

interface BillingBudget {
  service: string;
  actual_spend: number;
  allocated_budget: number;
  variance_percent: number;
  status: 'under_budget' | 'on_track' | 'over_budget';
}

interface BillingData {
  total_cost: number;
  top_service: string;
  services_count: number;
  cost_trends: CostTrend[];
  anomalies: BillingAnomaly[];
  budget_status: BillingBudget[];
  cost_spike_detected?: boolean;
  cost_spike_service?: string;
  cost_spike_amount?: number;
}

// ─── Helpers to convert BillingData → CloudHelm component types ─────────────

function toCloudHelmSummary(data: BillingData): CostSummaryResponse {
  // Group trends by service → series
  const seriesMap: Record<string, { date: string; total_cost: number }[]> = {};
  for (const t of data.cost_trends) {
    if (!seriesMap[t.service]) seriesMap[t.service] = [];
    seriesMap[t.service].push({ date: t.date, total_cost: t.amount });
  }
  const series = Object.entries(seriesMap).map(([key, points]) => ({
    key,
    points: points.sort((a, b) => a.date.localeCompare(b.date)),
  }));

  const allDates = data.cost_trends.map(t => t.date).sort();
  return {
    from: allDates[0] ?? new Date().toISOString().split('T')[0],
    to: allDates[allDates.length - 1] ?? new Date().toISOString().split('T')[0],
    group_by: 'service',
    series,
    total_cost: data.total_cost,
  };
}

function toCloudHelmAnomalies(data: BillingData): CostAnomaly[] {
  return data.anomalies.map((a, i) => ({
    id: i + 1,
    ts_date: a.date,
    cloud: 'aws',
    team: null,
    service: a.service,
    region: null,
    env: null,
    actual_cost: a.amount,
    expected_cost: a.expected_amount,
    anomaly_score: 1.0,
    direction: (a.anomaly_type === 'spike' ? 'spike' : 'drop') as 'spike' | 'drop',
    severity: (a.severity as 'low' | 'medium' | 'high') ?? 'medium',
  }));
}

function toCloudHelmBudgets(data: BillingData): BudgetStatus[] {
  return data.budget_status.map(b => {
    let status: 'UNDER' | 'AT_RISK' | 'OVER';
    if (b.status === 'under_budget') status = 'UNDER';
    else if (b.status === 'over_budget') status = 'OVER';
    else status = 'AT_RISK';

    return {
      team: b.service,
      service: b.service,
      monthly_budget: b.allocated_budget,
      mtd_cost: b.actual_spend,
      projected_cost: b.actual_spend,
      status,
      currency: 'USD',
    };
  });
}

// ─── Spike Banner ─────────────────────────────────────────────────────────────

function SpikeBanner({ data }: { data: BillingData }) {
  // Use the explicit spike fields from the API (mirrors feature_2 renderSpikeBanner)
  if (!data.cost_spike_detected || !data.cost_spike_service) return null;

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(n);

  const topAnomaly = data.anomalies.find(a => a.service === data.cost_spike_service);

  return (
    <div className="flex items-center gap-4 px-6 py-[18px] rounded-2xl mb-6 border animate-[slideIn_0.4s_ease]"
      style={{
        background: 'linear-gradient(135deg, rgba(248,113,113,0.12), rgba(251,191,36,0.08))',
        borderColor: 'rgba(248,113,113,0.35)',
      }}>
      <span className="text-3xl flex-shrink-0">🚨</span>
      <div>
        <div className="text-xs font-semibold uppercase tracking-widest text-red-400">Cost Spike Detected</div>
        <div className="text-base font-bold text-white mt-0.5">{data.cost_spike_service} cost spike detected</div>
        <div className="text-sm text-slate-400 mt-0.5">
          {topAnomaly?.description || 'Unusually high spend identified — review your usage patterns'}
        </div>
      </div>
      <div className="ml-auto px-3 py-1.5 rounded-full text-sm font-bold text-red-400 border border-red-500/40 bg-red-500/10 whitespace-nowrap">
        {fmt(data.cost_spike_amount ?? 0)} spike
      </div>
    </div>
  );
}

// ─── Extended Summary Cards (matches feature_2: Total, Top Service, Anomalies, Services, Over Budget) ──

function BillingSummaryCards({ data }: { data: BillingData }) {
  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(n);

  const overBudget = data.budget_status.filter(b => b.status === 'over_budget').length;

  const cards = [
    { icon: '💰', label: 'Total Spend', value: fmt(data.total_cost), sub: 'From uploaded CSV', accent: 'cyan' },
    { icon: '☁️', label: 'Top Service', value: data.top_service || '—', sub: 'Highest spend', accent: 'purple', small: true },
    { icon: '🔴', label: 'Anomalies', value: String(data.anomalies.length), sub: data.anomalies.length ? 'Issues found' : 'All clear', accent: 'red' },
    { icon: '📦', label: 'Services', value: String(data.services_count || data.budget_status.length), sub: 'Active services', accent: 'green' },
    { icon: '⚠️', label: 'Over Budget', value: String(overBudget), sub: 'Services over limit', accent: 'amber' },
  ];

  const accentMap: Record<string, { value: string; card: string }> = {
    cyan:   { value: 'bg-gradient-to-br from-cyan-300 to-sky-300 bg-clip-text text-transparent',   card: '' },
    purple: { value: 'bg-gradient-to-br from-violet-300 to-purple-300 bg-clip-text text-transparent', card: '' },
    red:    { value: 'text-red-400',   card: '' },
    green:  { value: 'text-emerald-400', card: '' },
    amber:  { value: 'text-amber-400', card: '' },
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      {cards.map((c, i) => (
        <div key={i} className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-5 hover:bg-slate-800/60 hover:border-slate-500 transition-all duration-300">
          <div className="flex items-start justify-between mb-1">
            <div className="text-[0.7rem] font-semibold uppercase tracking-widest text-slate-500">{c.label}</div>
            <span className="text-xl">{c.icon}</span>
          </div>
          <div className={`font-extrabold mt-1 leading-none ${c.small ? 'text-[1.15rem]' : 'text-[1.75rem]'} ${accentMap[c.accent].value}`}>
            {c.value}
          </div>
          <div className="text-xs text-slate-500 mt-1.5">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Enhanced Anomalies Table (matches feature_2 columns: Date, Service, Type, Actual, Expected, Severity, Description) ──

function BillingAnomaliesTable({ anomalies }: { data: BillingData; anomalies: BillingAnomaly[] }) {
  const fmt2 = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
  const fmtDate = (s: string) => {
    try { return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); } catch { return s; }
  };
  const typeIcon = (t: string) => ({ spike: '📈', drop: '📉', unusual_pattern: '🔀' }[t] ?? '❓');
  const severityColor: Record<string, string> = {
    low:      'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    medium:   'bg-orange-500/15 text-orange-400 border border-orange-500/30',
    high:     'bg-red-500/15 text-red-400 border border-red-500/30',
    critical: 'bg-red-600/25 text-red-300 border border-red-500/50',
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl mb-6">
      <div className="flex items-center justify-between px-6 py-[18px] border-b border-slate-700/60">
        <div>
          <div className="flex items-center gap-2 text-base font-semibold text-slate-100">
            <span className="inline-block w-[3px] h-4 rounded bg-gradient-to-b from-cyan-400 to-violet-500"></span>
            Cost Anomalies
          </div>
          <div className="text-xs text-slate-500 mt-0.5">Unusual spending patterns detected by Gemini AI</div>
        </div>
        <span className="text-xs text-slate-500 font-medium">{anomalies.length} detected</span>
      </div>

      {anomalies.length === 0 ? (
        <div className="text-center py-10 text-slate-400">
          <div className="text-3xl mb-2">🎉</div>
          <div className="font-semibold">No anomalies detected</div>
          <div className="text-sm text-slate-500 mt-1">Your spending patterns look normal</div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-white/[0.03]">
              <tr>
                {['Date', 'Service', 'Type', 'Actual', 'Expected', 'Severity', 'Description'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[0.7rem] font-semibold uppercase tracking-widest text-slate-500">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, i) => (
                <tr key={i} className="border-t border-white/[0.06] hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 text-sm text-slate-400 whitespace-nowrap">{fmtDate(a.date)}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-cyan-400 whitespace-nowrap">{a.service}</td>
                  <td className="px-4 py-3 text-sm text-slate-300 whitespace-nowrap">
                    {typeIcon(a.anomaly_type)} {(a.anomaly_type || '').replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-red-400 text-right whitespace-nowrap">{fmt2(a.amount)}</td>
                  <td className="px-4 py-3 text-sm text-slate-400 text-right whitespace-nowrap">{fmt2(a.expected_amount)}</td>
                  <td className="px-4 py-3 text-center whitespace-nowrap">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-[0.7rem] font-semibold ${severityColor[a.severity] ?? severityColor.low}`}>
                      {(a.severity || '').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-[260px]">{a.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Enhanced Budget Table (matches feature_2: Service, Actual, Budget, Variance Bar, Status) ──

function BillingBudgetTable({ budgets }: { budgets: BillingBudget[] }) {
  const fmt2 = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);

  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      under_budget: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
      on_track:     'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25',
      over_budget:  'bg-red-500/15 text-red-400 border border-red-500/30',
    };
    const labels: Record<string, string> = { under_budget: 'Under Budget', on_track: 'On Track', over_budget: 'Over Budget' };
    return { cls: map[s] ?? map.on_track, label: labels[s] ?? '—' };
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl mb-6">
      <div className="flex items-center justify-between px-6 py-[18px] border-b border-slate-700/60">
        <div>
          <div className="flex items-center gap-2 text-base font-semibold text-slate-100">
            <span className="inline-block w-[3px] h-4 rounded bg-gradient-to-b from-cyan-400 to-violet-500"></span>
            Budget Status
          </div>
          <div className="text-xs text-slate-500 mt-0.5">Per-service budget analysis</div>
        </div>
        <span className="text-xs text-slate-500 font-medium">{budgets.length} services</span>
      </div>

      {budgets.length === 0 ? (
        <div className="text-center py-10 text-slate-400">
          <div className="text-3xl mb-2">📋</div>
          <div className="font-semibold">No budget data</div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-white/[0.03]">
              <tr>
                {['Service', 'Actual Spend', 'Budget', 'Variance', 'Status'].map((h, i) => (
                  <th key={h} className={`px-4 py-3 text-[0.7rem] font-semibold uppercase tracking-widest text-slate-500 ${i > 0 ? 'text-right' : 'text-left'} ${h === 'Status' ? 'text-center' : ''}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {budgets.map((b, i) => {
                const pct = Math.min(Math.abs(b.variance_percent), 100);
                const varColor = b.variance_percent > 10 ? '#f87171' : b.variance_percent < -10 ? '#34d399' : '#22d3ee';
                const sign = b.variance_percent > 0 ? '+' : '';
                const { cls, label } = statusBadge(b.status);
                return (
                  <tr key={i} className="border-t border-white/[0.06] hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-sm font-semibold text-white">{b.service}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-white text-right">{fmt2(b.actual_spend)}</td>
                    <td className="px-4 py-3 text-sm text-slate-400 text-right">{fmt2(b.allocated_budget)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-xs font-semibold min-w-[48px] text-right" style={{ color: varColor }}>
                          {sign}{b.variance_percent.toFixed(1)}%
                        </span>
                        <div className="w-[70px] h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: varColor }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[0.7rem] font-semibold ${cls}`}>{label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Cost Trend Chart wrapper using existing component ───────────────────────

function BillingTrendChart({ data }: { data: BillingData }) {
  const costSummary = toCloudHelmSummary(data);
  const anomalies = toCloudHelmAnomalies(data);
  return <CostTimeSeriesChart costData={costSummary} anomalies={anomalies} loading={false} />;
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CostDashboard() {
  const [billingData, setBillingData] = useState<BillingData | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'loading' | 'success' | 'error'; text: string } | null>(null);
  const [dragging, setDragging] = useState(false);

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setStatusMsg({ type: 'error', text: '⚠ Please upload a .csv file' });
      return;
    }

    setAnalyzing(true);
    setBillingData(null);
    setStatusMsg({ type: 'loading', text: `Uploading "${file.name}" and running Gemini AI analysis…` });

    try {
      const result = await api.analyzeBillingCsv(file);
      const data: BillingData = result.data;
      setBillingData(data);
      setStatusMsg({ type: 'success', text: `✓ Analysis complete for "${file.name}"` });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: `✗ Analysis failed: ${err.message || 'Unknown error'}` });
    } finally {
      setAnalyzing(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = '';
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  // Status bar colours
  const statusStyle: Record<string, string> = {
    loading: 'bg-cyan-500/10 border border-cyan-500/25 text-cyan-400',
    success: 'bg-emerald-500/10 border border-emerald-500/25 text-emerald-400',
    error:   'bg-red-500/10 border border-red-500/25 text-red-400',
  };

  return (
    <div className="p-6 min-h-screen bg-[#020204]"
      style={{
        backgroundImage:
          'radial-gradient(ellipse 80% 60% at 10% -10%, rgba(34,211,238,0.06) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 90% 100%, rgba(167,139,250,0.05) 0%, transparent 60%)',
      }}>
      <div className="max-w-7xl mx-auto">

        {/* Page Header */}
        <div className="mb-7 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-white">💰 Cost &amp; Health Dashboard</h1>
            <p className="text-slate-400 mt-1.5 text-sm">
              Upload your AWS billing CSV — Gemini AI extracts cost trends, anomalies, and budget status instantly.
            </p>
          </div>
          <button 
            onClick={async () => {
              try {
                const [relData, healthData] = await Promise.all([
                  api.getReliabilityMetrics(),
                  api.getHealthSummary()
                ]);
                const systemStatus = healthData.some(s => s.status === 'critical' || s.status === 'warning') ? 'Degraded' : 
                                     healthData.some(s => s.status === 'degraded') ? 'Partially Degraded' : 'Healthy';
                generateSLAPDF(relData, healthData, systemStatus);
              } catch (e) {
                console.error("Error generating PDF:", e);
                alert("Could not fetch SLA data from backend.");
              }
            }}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 text-cyan-400 hover:from-cyan-500/30 hover:to-purple-500/30 transition-all font-medium hover:shadow-[0_0_15px_rgba(34,211,238,0.2)]"
          >
            <Download size={18} />
            Export SLA Report
          </button>
        </div>

        {/* Upload Zone */}
        <div className="mb-7">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-3">
            <span className="inline-block w-[3px] h-4 rounded bg-gradient-to-b from-cyan-400 to-violet-500"></span>
            Upload Billing CSV
          </div>

          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`relative border-2 border-dashed rounded-2xl py-12 px-8 text-center cursor-pointer transition-all duration-200 ${
              dragging
                ? 'border-cyan-400 bg-cyan-400/10'
                : 'border-slate-600 hover:border-cyan-500/60 hover:bg-cyan-500/5 bg-cyan-500/[0.02]'
            }`}
          >
            <input
              type="file"
              accept=".csv"
              onChange={onFileChange}
              disabled={analyzing}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
            />
            <div className="text-5xl mb-3">📂</div>
            <div className="text-base font-semibold text-slate-100">Drag &amp; drop your AWS billing CSV here</div>
            <div className="text-sm text-slate-500 mt-1">Or click to browse · Supports AWS Cost &amp; Usage Report format</div>
            <div className="inline-flex items-center gap-2 mt-5 px-5 py-2 rounded-full border border-cyan-400/40 bg-cyan-400/10 text-cyan-400 text-sm font-semibold pointer-events-none">
              📤 Choose CSV File
            </div>
          </div>

          {/* Status bar */}
          {statusMsg && (
            <div className={`flex items-center gap-3 mt-4 px-5 py-3.5 rounded-xl text-sm font-medium ${statusStyle[statusMsg.type]}`}>
              {statusMsg.type === 'loading' && (
                <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin flex-shrink-0" />
              )}
              <span>{statusMsg.text}</span>
            </div>
          )}
        </div>

        {/* Placeholder */}
        {!billingData && !analyzing && (
          <div className="text-center py-16 text-slate-500">
            <div className="text-6xl mb-4 opacity-70">📊</div>
            <h2 className="text-lg font-bold text-slate-400">Your dashboard will appear here</h2>
            <p className="text-sm text-slate-600 mt-1.5">
              Upload a billing CSV above to see cost trends, anomalies, and budget analysis powered by Gemini AI.
            </p>
          </div>
        )}

        {/* Loading skeleton */}
        {analyzing && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="relative w-20 h-20 mx-auto mb-6">
                <div className="absolute inset-0 bg-white/5 rounded-full backdrop-blur-xl border border-white/10" />
                <div className="absolute inset-0 border-4 border-transparent border-t-cyan-400/50 rounded-full animate-spin" />
                <div className="absolute inset-3 border-4 border-transparent border-t-violet-400/40 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
              </div>
              <p className="text-slate-300 font-medium">Analyzing with Gemini AI…</p>
            </div>
          </div>
        )}

        {/* Dashboard */}
        {billingData && (
          <>
            {/* Cost Spike Banner */}
            <SpikeBanner data={billingData} />

            {/* 5-card Summary */}
            <BillingSummaryCards data={billingData} />

            {/* Cost Trend Chart */}
            <BillingTrendChart data={billingData} />

            {/* Anomalies Table */}
            <BillingAnomaliesTable data={billingData} anomalies={billingData.anomalies} />

            {/* Budget Table */}
            <BillingBudgetTable budgets={billingData.budget_status} />
          </>
        )}

      </div>
    </div>
  );
}
