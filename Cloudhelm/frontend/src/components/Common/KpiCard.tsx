import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface KpiCardProps {
  title: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  trend?: Array<{ value: number }>;
}

export default function KpiCard({ 
  title, 
  value, 
  delta, 
  deltaType, 
  icon: Icon, 
  trend 
}: KpiCardProps) {
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
          <span className={`text-xs font-semibold ${
            isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-slate-400'
          }`}>
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
