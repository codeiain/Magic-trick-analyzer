import { ReactNode } from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: {
    value: number;
    label: string;
    type: 'increase' | 'decrease' | 'neutral';
  };
  className?: string;
}

export default function StatsCard({ title, value, icon, trend, className = '' }: StatsCardProps) {
  const getTrendColor = (type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase':
        return 'text-green-600';
      case 'decrease':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className={`bg-white/80 backdrop-blur-lg p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 ${className}`}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="flex items-center justify-center h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25">
            <span className="text-xl">{icon}</span>
          </div>
        </div>
        <div className="ml-4 w-0 flex-1">
          <dl>
            <dt className="text-sm font-semibold text-slate-600 truncate">
              {title}
            </dt>
            <dd className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
              {value}
            </dd>
          </dl>
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center text-sm backdrop-blur-sm bg-white/40 rounded-xl px-3 py-2 border border-white/30">
          <span className={`font-semibold ${getTrendColor(trend.type)}`}>
            {trend.type === 'increase' ? '+' : trend.type === 'decrease' ? '-' : ''}
            {Math.abs(trend.value)}%
          </span>
          <span className="text-slate-600 ml-2 font-medium">
            {trend.label}
          </span>
        </div>
      )}
    </div>
  );
}
