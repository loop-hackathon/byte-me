import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { 
  Activity, 
  Search, 
  RefreshCw, 
  Terminal, 
  Clock, 
  Database, 
  Globe, 
  Server, 
  AlertCircle
} from 'lucide-react';

interface Span {
  name: string;
  kind: string;
  startTimeUnixNano: string;
  endTimeUnixNano: string;
  attributes?: { key: string; value: any }[];
  status?: { code: number };
  parentSpanId?: string;
  spanId: string;
}

interface Trace {
  traceID: string;
  durationMs: number;
  startTimeUnixNano: string;
  batches?: any[]; 
}

export function TracingView() {
  const [traces, setTraces] = useState<any[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProject, setSelectedProject] = useState('');

  useEffect(() => {
    loadTraces();
  }, []);

  const loadTraces = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listTraces(30, selectedProject);
      setTraces(data.traces || []);
    } catch (err) {
      console.error('Error loading traces:', err);
      setError('Failed to load traces. Is the observability stack running?');
    } finally {
      setLoading(false);
    }
  };

  const loadTraceDetail = async (traceId: string) => {
    try {
      setLoadingDetail(true);
      const data = await api.getTrace(traceId);
      setSelectedTrace(data);
    } catch (err) {
      console.error('Error loading trace detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getServiceIcon = (name: string) => {
    if (name.includes('frontend')) return <Globe className="w-4 h-4 text-cyan-400" />;
    if (name.includes('backend')) return <Server className="w-4 h-4 text-blue-400" />;
    if (name.includes('db') || name.includes('sql')) return <Database className="w-4 h-4 text-purple-400" />;
    return <Activity className="w-4 h-4 text-slate-400" />;
  };

  const formatDuration = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const flattenSpans = (traceData: any): any[] => {
    const spans: any[] = [];
    if (!traceData?.batches) return [];

    traceData.batches.forEach((batch: any) => {
      const serviceName = batch.resource?.attributes?.find((a: any) => a.key === 'service.name')?.value?.stringValue || 'unknown';
      
      batch.scopeSpans?.forEach((scope: any) => {
        scope.spans?.forEach((span: any) => {
          spans.push({
            ...span,
            serviceName,
            start: parseInt(span.startTimeUnixNano),
            end: parseInt(span.endTimeUnixNano),
            duration: (parseInt(span.endTimeUnixNano) - parseInt(span.startTimeUnixNano)) / 1000000
          });
        });
      });
    });

    return spans.sort((a, b) => a.start - b.start);
  };

  const filteredTraces = traces.filter(t => 
    t.traceID.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="text-cyan-400 w-5 h-5" />
            Distributed Tracing
          </h2>
          <p className="text-sm text-slate-400 mt-1">Visualize request waterfalls</p>
        </div>
        <div className="flex items-center gap-3">
          <input 
            type="text"
            placeholder="Filter by Project Name..."
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadTraces()}
            className="w-48 px-3 py-1.5 bg-slate-900/50 border border-slate-700 focus:border-cyan-500 rounded-lg text-sm text-slate-200 outline-none transition-all"
          />
          <button 
            onClick={loadTraces}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/60 border border-slate-700 hover:border-cyan-500/50 rounded-lg text-sm text-slate-200 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
          <div>
            <p className="text-red-400 font-medium">Observability Stack Offline</p>
            <p className="text-red-400/70 text-sm mt-1">
              Make sure to run <code>docker compose -f docker-compose.observability.yml up -d</code> to see real traces.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="col-span-1 flex flex-col gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text"
              placeholder="Search trace ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-900/50 border border-slate-700 focus:border-cyan-500 rounded-lg text-sm text-slate-200 outline-none transition-all"
            />
          </div>

          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl overflow-hidden flex-1 shadow-2xl">
            <div className="p-3 border-b border-slate-700 bg-slate-900/80 font-medium text-xs text-slate-500 uppercase tracking-wider">
              Recent Traces
            </div>
            <div className="max-h-[500px] overflow-y-auto custom-scrollbar">
              {loading && (
                <div className="p-8 text-center text-slate-500 text-sm italic">Loading traces...</div>
              )}
              {!loading && filteredTraces.length === 0 && (
                <div className="p-8 text-center text-slate-500 text-sm italic">No recent traces found</div>
              )}
              {filteredTraces.map((trace) => (
                <div 
                  key={trace.traceID}
                  onClick={() => loadTraceDetail(trace.traceID)}
                  className={`p-3 border-b border-slate-700/50 cursor-pointer transition-all hover:bg-slate-800 ${
                    selectedTrace?.traceID === trace.traceID ? 'bg-cyan-500/10 border-l-4 border-l-cyan-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-cyan-400/80">{trace.traceID.slice(0, 12)}...</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      trace.durationMs > 500 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                    }`}>
                      {formatDuration(trace.durationMs)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mt-2">
                    <Clock className="w-3 h-3" />
                    {new Date(parseInt(trace.startTimeUnixNano) / 1000000).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-1 lg:col-span-2">
          <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl min-h-[500px] flex flex-col shadow-2xl">
            {!selectedTrace && !loadingDetail && (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
                <Terminal className="w-10 h-10 mb-3 text-slate-600" />
                <p className="text-base font-medium text-slate-400">Select a trace to visualize the waterfall</p>
                <p className="text-xs mt-2 max-w-sm">
                  Tracing allows you to see exactly where time is being spent in a request.
                </p>
              </div>
            )}

            {loadingDetail && (
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mb-3"></div>
                <p className="text-sm text-slate-400 animate-pulse">Fetching trace details...</p>
              </div>
            )}

            {selectedTrace && !loadingDetail && (
              <div className="p-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex items-center justify-between border-b border-slate-700 pb-4 mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-100 mb-1">Trace Waterfall</h3>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-mono text-slate-500">ID: {selectedTrace.traceID}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-cyan-400">{formatDuration(selectedTrace.durationMs)}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-0.5">Total Duration</div>
                  </div>
                </div>

                <div className="space-y-3">
                  {(() => {
                    const spans = flattenSpans(selectedTrace);
                    if (spans.length === 0) return <div className="text-center py-8 text-slate-500 italic text-sm">No span data available</div>;

                    const findSlowestSpan = () => {
                      let slowest = spans[0];
                      spans.forEach(s => {
                        if (s.duration > slowest.duration) slowest = s;
                      });
                      return slowest;
                    };

                    const slowest = findSlowestSpan();
                    const firstStart = spans[0].start;
                    const lastEnd = Math.max(...spans.map(s => s.end));
                    const totalSpanDuration = lastEnd - firstStart;

                    return (
                      <>
                        <div className="p-3 bg-orange-500/5 border border-orange-500/20 rounded-lg mb-4">
                          <div className="flex items-center gap-1.5 mb-1.5 text-orange-400 text-[10px] font-semibold uppercase tracking-wider">
                            <AlertCircle className="w-3 h-3" />
                            Slowest Component
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-300">
                              <span className="text-slate-500">Service:</span> {slowest.serviceName} 
                              <span className="mx-2 text-slate-700">|</span> 
                              <span className="text-slate-500">Span:</span> {slowest.name}
                            </span>
                            <span className="text-orange-400 text-xs font-bold">{formatDuration(slowest.duration)}</span>
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          {spans.map((span, idx) => {
                            const relativeStart = ((span.start - firstStart) / totalSpanDuration) * 100;
                            const width = (span.duration / (totalSpanDuration / 1000000)) * 100;

                            const isFrontend = span.serviceName.includes('frontend');
                            const isDB = span.serviceName.includes('db') || span.name.startsWith('SELECT') || span.name.startsWith('INSERT');
                            const barColor = isFrontend ? 'bg-cyan-500' : isDB ? 'bg-purple-500' : 'bg-blue-500';

                            return (
                              <div key={span.spanId} className="group flex flex-col gap-0.5">
                                <div className="flex items-center justify-between text-[10px] px-1">
                                  <div className="flex items-center gap-1.5 text-slate-300">
                                    {getServiceIcon(span.serviceName)}
                                    <span className="text-slate-500 italic">{span.serviceName}</span>
                                    <span className="group-hover:text-cyan-400 transition-colors truncate max-w-[200px]">{span.name}</span>
                                  </div>
                                  <div className="text-slate-500 group-hover:text-slate-300 transition-colors">
                                    {formatDuration(span.duration)}
                                  </div>
                                </div>
                                <div className="relative h-4 bg-slate-800/40 rounded overflow-hidden group-hover:bg-slate-800/60 transition-colors">
                                  <div 
                                    className={`absolute top-0 bottom-0 ${barColor} rounded-sm transition-all duration-500`}
                                    style={{ 
                                      left: `${Math.max(0, Math.min(99, relativeStart))}%`, 
                                      width: `${Math.max(1, Math.min(100 - relativeStart, width))}%`,
                                      opacity: 0.8
                                    }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
      `}} />
    </div>
  );
}
