import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

interface AlertBannerProps {
  type?: 'info' | 'warning' | 'error' | 'success';
  title?: string;
  children: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'info',
  title,
  children,
  onDismiss,
  className = '',
}) => {
  const styles = {
    info: {
      bg: 'bg-sky-50 border-sky-200 text-sky-900',
      icon: <Info className="w-5 h-5 text-sky-600 flex-shrink-0" />,
    },
    warning: {
      bg: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />,
    },
    error: {
      bg: 'bg-rose-50 border-rose-200 text-rose-900',
      icon: <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />,
    },
    success: {
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      icon: <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />,
    },
  }[type];

  return (
    <div className={`p-4 rounded-xl border flex items-start gap-3 text-sm ${styles.bg} ${className}`}>
      {styles.icon}
      <div className="flex-1">
        {title && <h4 className="font-semibold text-sm mb-1">{title}</h4>}
        <div className="text-xs sm:text-sm leading-relaxed">{children}</div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-slate-400 hover:text-slate-600 rounded p-1 hover:bg-slate-200/50"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
