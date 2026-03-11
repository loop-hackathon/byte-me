// Dashboard Preview Component
export function DashboardPreview() {
  return (
    <div className="w-full max-w-6xl z-20 mt-[-20px] relative perspective-1000 animate-enter delay-400">
      <div className="glass-surface border border-white/20 rounded-t-2xl overflow-hidden backdrop-blur-md shadow-[0_0_80px_rgba(34,211,238,0.15)] relative">
        <div className="glass-top-border"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDIpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-[0.03] mix-blend-overlay pointer-events-none"></div>

        {/* Header Bar */}
        <div className="flex bg-black/20 border-b border-white/5 pt-4 px-6 pb-4 items-center justify-between relative z-10">
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/40"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/40"></div>
            </div>
            <div className="h-4 w-px bg-white/10 mx-2"></div>
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              <span>CLOUDHELM</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-300">COST_DASHBOARD</span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
            <span className="text-[10px] font-semibold text-cyan-300 tracking-wide">LIVE</span>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex h-[500px] relative z-10">
          {/* Sidebar */}
          <div className="flex flex-col gap-6 bg-black/10 w-16 border-r border-white/5 pt-6 pb-6 items-center">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2" />
              </svg>
            </div>
            <div className="p-2.5 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors cursor-pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="20" height="8" x="2" y="2" rx="2" ry="2" />
                <rect width="20" height="8" x="2" y="14" rx="2" ry="2" />
                <line x1="6" x2="6.01" y1="6" y2="6" />
                <line x1="6" x2="6.01" y1="18" y2="18" />
              </svg>
            </div>
            <div className="p-2.5 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors cursor-pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                <path d="M2 12h20" />
              </svg>
            </div>
            <div className="mt-auto p-2.5 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors cursor-pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 7h-9" />
                <path d="M14 17H5" />
                <circle cx="17" cy="17" r="3" />
                <circle cx="7" cy="7" r="3" />
              </svg>
            </div>
          </div>

          {/* Main Grid */}
          <div className="flex-1 grid grid-cols-12 gap-4 p-6">
            {/* Stats Row */}
            <div className="col-span-12 grid grid-cols-3 gap-4 h-28">
              <div className="rounded-xl border border-white/5 bg-white/[0.03] p-4 flex flex-col justify-between group hover:border-cyan-500/30 transition-all hover:bg-cyan-500/[0.05]">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Total Cost</p>
                    <h3 className="text-xl font-bold text-white tracking-tight">$24,891</h3>
                  </div>
                  <div className="text-cyan-400 bg-cyan-500/10 rounded-md p-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="12" x2="12" y1="2" y2="22" />
                      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                    </svg>
                  </div>
                </div>
                <div className="w-full bg-white/5 rounded-full h-1 overflow-hidden mt-2">
                  <div className="bg-cyan-400 h-full rounded-full" style={{ width: '68%' }}></div>
                </div>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.03] p-4 flex flex-col justify-between group hover:border-cyan-500/30 transition-all hover:bg-cyan-500/[0.05]">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Anomalies</p>
                    <h3 className="text-xl font-bold text-white tracking-tight">3</h3>
                  </div>
                  <div className="text-red-400 bg-red-500/10 rounded-md p-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                      <path d="M12 9v4" />
                      <path d="M12 17h.01" />
                    </svg>
                  </div>
                </div>
                <div className="flex gap-1 mt-2">
                  <div className="flex-1 bg-red-500/20 rounded-full h-1"></div>
                  <div className="flex-1 bg-red-500/20 rounded-full h-1"></div>
                  <div className="flex-1 bg-white/5 rounded-full h-1"></div>
                </div>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.03] p-4 flex flex-col justify-between group hover:border-cyan-500/30 transition-all hover:bg-cyan-500/[0.05]">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Budget Status</p>
                    <h3 className="text-xl font-bold text-white tracking-tight">78%</h3>
                  </div>
                  <div className="text-emerald-400 bg-emerald-500/10 rounded-md p-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                      <polyline points="3.29 7 12 12 20.71 7" />
                      <line x1="12" x2="12" y1="22" y2="12" />
                    </svg>
                  </div>
                </div>
                <div className="w-full bg-white/5 rounded-full h-1 overflow-hidden mt-2">
                  <div className="bg-emerald-400 h-full rounded-full" style={{ width: '78%' }}></div>
                </div>
              </div>
            </div>

            {/* Chart Area */}
            <div className="col-span-8 rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <div className="flex justify-between items-center mb-3">
                <h4 className="text-xs font-semibold text-white">Cost Trend</h4>
                <div className="flex gap-1">
                  <button className="text-[10px] px-2 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">7D</button>
                  <button className="text-[10px] px-2 py-1 rounded-md text-slate-400 hover:text-white">30D</button>
                  <button className="text-[10px] px-2 py-1 rounded-md text-slate-400 hover:text-white">90D</button>
                </div>
              </div>
              <div className="h-40 flex items-end justify-between gap-1.5">
                {[65, 72, 68, 85, 78, 92, 88].map((height, i) => (
                  <div key={i} className="flex-1 bg-gradient-to-t from-cyan-500/20 to-cyan-500/5 rounded-t-lg relative group cursor-pointer" style={{ height: `${height}%` }}>
                    <div className="absolute inset-x-0 top-0 h-1 bg-cyan-400 rounded-t-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  </div>
                ))}
              </div>
            </div>

            {/* Event Log Panel */}
            <div className="col-span-4 bg-white/[0.02] border border-white/5 rounded-xl flex flex-col">
              <div className="p-3 border-b border-white/5 flex justify-between items-center">
                <h4 className="text-[10px] font-semibold text-white">Event Log</h4>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1 text-[10px]">
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group">
                  <span className="text-slate-600">10:42:01</span>
                  <span className="text-cyan-400">INFO</span>
                  <span className="group-hover:text-white transition-colors truncate">Backup initialized</span>
                </div>
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group">
                  <span className="text-slate-600">10:42:05</span>
                  <span className="text-emerald-400">SUCCESS</span>
                  <span className="group-hover:text-white transition-colors truncate">Node synced</span>
                </div>
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group">
                  <span className="text-slate-600">10:42:12</span>
                  <span className="text-red-400">ALERT</span>
                  <span className="group-hover:text-white transition-colors truncate">Cost spike detected</span>
                </div>
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group">
                  <span className="text-slate-600">10:42:18</span>
                  <span className="text-cyan-400">INFO</span>
                  <span className="group-hover:text-white transition-colors truncate">Health check passed</span>
                </div>
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group opacity-50">
                  <span className="text-slate-600">10:42:22</span>
                  <span className="text-cyan-400">INFO</span>
                  <span className="group-hover:text-white transition-colors truncate">User authenticated</span>
                </div>
                <div className="flex gap-2 items-center text-slate-400 p-1.5 hover:bg-white/5 rounded cursor-pointer group opacity-50">
                  <span className="text-slate-600">10:42:28</span>
                  <span className="text-cyan-400">INFO</span>
                  <span className="group-hover:text-white transition-colors truncate">Data sync complete</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
