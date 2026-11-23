import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from './Card';
import { cn } from '../../lib/utils';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  trendUp?: boolean;
  icon: LucideIcon;
  color?: 'cyan' | 'sapphire' | 'emerald' | 'amber' | 'violet';
}

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendUp = true,
  icon: Icon,
  color = 'cyan',
}: MetricCardProps) {
  const colorBorders = {
    cyan: 'border-cyan-500/20 text-cyan-400 bg-cyan-950/30',
    sapphire: 'border-blue-500/20 text-blue-400 bg-blue-950/30',
    emerald: 'border-emerald-500/20 text-emerald-400 bg-emerald-950/30',
    amber: 'border-amber-500/20 text-amber-400 bg-amber-950/30',
    violet: 'border-violet-500/20 text-violet-400 bg-violet-950/30',
  };

  return (
    <Card className="p-5 flex items-start justify-between relative overflow-hidden group hover:border-slate-700 transition">
      <div className="space-y-1.5">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</div>
        <div className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{value}</div>
        {(subtitle || trend) && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400 pt-0.5">
            {trend && (
              <span className={cn('flex items-center font-semibold text-[11px]', trendUp ? 'text-emerald-400' : 'text-red-400')}>
                {trendUp ? <TrendingUp className="h-3 w-3 mr-0.5" /> : <TrendingDown className="h-3 w-3 mr-0.5" />}
                {trend}
              </span>
            )}
            {subtitle && <span>{subtitle}</span>}
          </div>
        )}
      </div>

      <div className={cn('p-3 rounded-xl border shrink-0', colorBorders[color])}>
        <Icon className="h-6 w-6" />
      </div>
    </Card>
  );
}
