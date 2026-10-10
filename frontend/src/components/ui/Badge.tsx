import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'critical' | 'high' | 'medium' | 'low' | 'success' | 'failed' | 'open' | 'investigating' | 'resolved' | 'neutral' | 'outline';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}) => {
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  const variantClasses = {
    critical: 'bg-rose-50 text-rose-700 border border-rose-200 font-semibold',
    high: 'bg-amber-50 text-amber-800 border border-amber-200 font-medium',
    medium: 'bg-sky-50 text-sky-700 border border-sky-200 font-medium',
    low: 'bg-slate-100 text-slate-700 border border-slate-200 font-normal',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    failed: 'bg-rose-50 text-rose-700 border border-rose-200 font-medium',
    open: 'bg-amber-100 text-amber-900 border border-amber-300 font-semibold',
    investigating: 'bg-sky-100 text-sky-800 border border-sky-300 font-semibold',
    resolved: 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
    outline: 'bg-white text-slate-600 border border-slate-300',
  }[variant] || 'bg-slate-100 text-slate-700';

  return (
    <span
      className={`inline-flex items-center rounded-md font-mono tracking-tight transition-colors ${sizeClasses} ${variantClasses} ${className}`}
    >
      {children}
    </span>
  );
};
