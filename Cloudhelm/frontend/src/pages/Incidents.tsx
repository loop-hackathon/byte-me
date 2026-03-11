import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import type { Incident, IncidentCreate } from '../types/incident';
import ReactMarkdown from 'react-markdown';

export default function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  useEffect(() => {
    loadIncidents();
  }, [filterStatus, filterSeverity]);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filterStatus !== 'all') params.status = filterStatus;
      if (filterSeverity !== 'all') params.severity = filterSeverity;
      
      const data = await api.listIncidents(params);
      setIncidents(data);
    } catch (error) {
      console.error('Error loading incidents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async (incident: Incident) => {
    try {
      setGeneratingSummary(true);
      const response = await api.generateIncidentSummary(incident.id);
      
      // Reload the incident to get the updated summary
      const updated = await api.getIncident(incident.id);
      setSelectedIncident(updated);
      
      // Update in list
      setIncidents(incidents.map(i => i.id === incident.id ? updated : i));
    } catch (error) {
      console.error('Error generating summary:', error);
      alert('Failed to generate AI summary. Check if GEMINI_API_KEY is configured.');
    } finally {
      setGeneratingSummary(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      low: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
      high: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
      critical: 'text-red-400 bg-red-500/10 border-red-500/30'
    };
    return colors[severity as keyof typeof colors] || colors.medium;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      investigating: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
      identified: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
      monitoring: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      resolved: 'text-green-400 bg-green-500/10 border-green-500/30'
    };
    return colors[status as keyof typeof colors] || colors.investigating;
  };

  return (
    <div className="p-6 min-h-screen bg-[#020204]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">Incidents</h1>
          <p className="text-slate-400 mt-1">Track and manage production incidents with AI-powered analysis</p>
        </div>

        {/* Filters */}
        <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 text-slate-100"
                >
                  <option value="all">All</option>
                  <option value="investigating">Investigating</option>
                  <option value="identified">Identified</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Severity</label>
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="px-3 py-2 bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500 text-slate-100"
                >
                  <option value="all">All</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <button
              onClick={() => setShowCreateForm(true)}
              className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-medium transition-colors"
            >
              + New Incident
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
          </div>
        )}

        {/* Incidents List */}
        {!loading && incidents.length === 0 && (
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-12 text-center">
            <div className="text-6xl mb-4">🚨</div>
            <h3 className="text-xl font-semibold text-white mb-2">No incidents found</h3>
            <p className="text-slate-400 mb-6">Create your first incident to get started</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-medium transition-colors"
            >
              Create Incident
            </button>
          </div>
        )}

        {!loading && incidents.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Incidents List */}
            <div className="space-y-4">
              {incidents.map((incident) => (
                <div
                  key={incident.id}
                  onClick={() => setSelectedIncident(incident)}
                  className={`bg-slate-900/60 backdrop-blur-lg border rounded-xl shadow-xl p-4 cursor-pointer transition-all ${
                    selectedIncident?.id === incident.id
                      ? 'border-cyan-500 ring-2 ring-cyan-500/20'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{incident.title}</h3>
                      <p className="text-sm text-slate-400">{incident.incident_id}</p>
                    </div>
                    <div className="flex gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(incident.severity)}`}>
                        {incident.severity.toUpperCase()}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(incident.status)}`}>
                        {incident.status.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {incident.service && (
                    <div className="flex items-center gap-4 text-sm text-slate-400 mb-2">
                      <span>🔧 {incident.service}</span>
                      {incident.env && <span>📍 {incident.env}</span>}
                    </div>
                  )}

                  <div className="text-sm text-slate-400">
                    Created: {new Date(incident.created_at).toLocaleString()}
                  </div>

                  {incident.ai_summary && (
                    <div className="mt-2 flex items-center gap-2 text-sm text-cyan-400">
                      <span>✨</span>
                      <span>AI Summary Available</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Incident Details */}
            {selectedIncident && (
              <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl shadow-xl p-6 sticky top-6 max-h-[calc(100vh-8rem)] overflow-y-auto">
                <div className="mb-4">
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedIncident.title}</h2>
                  <p className="text-slate-400">{selectedIncident.incident_id}</p>
                </div>

                {selectedIncident.description && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">Description</h3>
                    <p className="text-slate-400">{selectedIncident.description}</p>
                  </div>
                )}

                {/* AI Summary Section */}
                <div className="mb-6">
                  {!selectedIncident.ai_summary ? (
                    <button
                      onClick={() => handleGenerateSummary(selectedIncident)}
                      disabled={generatingSummary}
                      className="w-full px-4 py-3 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    >
                      {generatingSummary ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Generating AI Summary...</span>
                        </>
                      ) : (
                        <>
                          <span>✨</span>
                          <span>Generate AI Summary</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                          <span>✨</span>
                          <span>AI-Generated Summary</span>
                        </h3>
                        <button
                          onClick={() => handleGenerateSummary(selectedIncident)}
                          disabled={generatingSummary}
                          className="text-xs text-slate-400 hover:text-cyan-400 transition-colors"
                        >
                          Regenerate
                        </button>
                      </div>
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{selectedIncident.ai_summary}</ReactMarkdown>
                      </div>
                      {selectedIncident.summary_generated_at && (
                        <p className="text-xs text-slate-500 mt-3">
                          Generated: {new Date(selectedIncident.summary_generated_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Raw Data */}
                <div className="space-y-4">
                  {selectedIncident.anomalies && (
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-2">Anomalies</h3>
                      <pre className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-400 whitespace-pre-wrap">
                        {selectedIncident.anomalies}
                      </pre>
                    </div>
                  )}

                  {selectedIncident.metrics_summary && (
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-2">Metrics Summary</h3>
                      <pre className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-400 whitespace-pre-wrap">
                        {selectedIncident.metrics_summary}
                      </pre>
                    </div>
                  )}

                  {selectedIncident.recent_releases && (
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-2">Recent Releases</h3>
                      <pre className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-400 whitespace-pre-wrap">
                        {selectedIncident.recent_releases}
                      </pre>
                    </div>
                  )}

                  {selectedIncident.cost_changes && (
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-2">Cost Impact</h3>
                      <pre className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-400 whitespace-pre-wrap">
                        {selectedIncident.cost_changes}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
