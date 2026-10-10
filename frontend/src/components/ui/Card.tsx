import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hoverable = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-slate-200/80 shadow-[0_1px_3px_rgba(15,23,42,0.04)] ${
        hoverable ? 'hover:border-slate-300 hover:shadow-md cursor-pointer transition-all' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, action, className = '' }) => {
  return (
    <div className={`p-4 sm:p-5 border-b border-slate-100 flex items-start justify-between gap-4 ${className}`}>
      <div>
        <h3 className="font-semibold text-slate-900 text-sm sm:text-base leading-tight">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500 mt-1 leading-normal">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};

export const CardBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return <div className={`p-4 sm:p-5 ${className}`}>{children}</div>;
};
