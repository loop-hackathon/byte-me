import React from 'react';

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  action?: React.ReactNode; // For "View All" links
}

export default function SectionCard({ 
  title, 
  subtitle, 
  children, 
  action 
}: SectionCardProps) {
  return (
    <div className="bg-slate-900/60 backdrop-blur-lg border border-slate-700 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
          {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}
