import React from 'react';
import { cn } from '../../lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'cyan' | 'sapphire' | 'emerald' | 'amber' | 'violet' | 'slate' | 'danger';
  size?: 'sm' | 'md';
}

export function Badge({ className, variant = 'slate', size = 'sm', children, ...props }: BadgeProps) {
  const variants = {
    cyan: 'bg-cyan-950/60 text-cyan-300 border-cyan-500/30 ring-1 ring-cyan-500/20',
    sapphire: 'bg-blue-950/60 text-blue-300 border-blue-500/30 ring-1 ring-blue-500/20',
    emerald: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30 ring-1 ring-emerald-500/20',
    amber: 'bg-amber-950/60 text-amber-300 border-amber-500/30 ring-1 ring-amber-500/20',
    violet: 'bg-violet-950/60 text-violet-300 border-violet-500/30 ring-1 ring-violet-500/20',
    slate: 'bg-slate-800/80 text-slate-300 border-slate-700/80',
    danger: 'bg-red-950/60 text-red-300 border-red-500/30 ring-1 ring-red-500/20',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded font-medium border select-none',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
