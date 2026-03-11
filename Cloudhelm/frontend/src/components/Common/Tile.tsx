import React, { ReactNode } from 'react';

interface TileProps {
  title: string;
  subtitle?: string;
  value?: string | number;
  trend?: ReactNode;
  extraInfo?: string;
  onClick?: () => void;
  loading?: boolean;
}

export default function Tile({
  title,
  subtitle,
  value,
  trend,
  extraInfo,
  onClick,
  loading = false
}: TileProps) {
  const Component = onClick ? 'button' : 'div';

  return (
    <Component
      onClick={onClick}
      className={`bg-white rounded-lg shadow p-6 ${
        onClick ? 'hover:shadow-lg transition-shadow cursor-pointer' : ''
      }`}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {value !== undefined && (
              <div className="text-3xl font-bold text-gray-900 mb-4">
                {value}
              </div>
            )}

            {trend && (
              <div className="mb-4">
                {trend}
              </div>
            )}

            {extraInfo && (
              <div className="text-sm text-gray-600 mt-auto">
                {extraInfo}
              </div>
            )}
          </>
        )}
      </div>
    </Component>
  );
}
