import React from 'react';

interface KpiGridProps {
  children: React.ReactNode;
}

export default function KpiGrid({ children }: KpiGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {children}
    </div>
  );
}
