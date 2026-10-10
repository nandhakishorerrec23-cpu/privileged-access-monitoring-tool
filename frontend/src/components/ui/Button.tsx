import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-3.5 py-2 text-sm',
    lg: 'px-4.5 py-2.5 text-base',
  }[size];

  const variantClasses = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800 focus-visible:ring-brand-500 shadow-sm border border-transparent',
    secondary: 'bg-slate-800 text-white hover:bg-slate-900 active:bg-black focus-visible:ring-slate-700 shadow-sm border border-transparent',
    outline: 'bg-white text-slate-700 hover:bg-slate-50 active:bg-slate-100 border border-slate-300 focus-visible:ring-slate-400 shadow-sm',
    danger: 'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 focus-visible:ring-rose-500 shadow-sm border border-transparent',
    ghost: 'text-slate-600 hover:bg-slate-100 active:bg-slate-200 border border-transparent focus-visible:ring-slate-400',
  }[variant];

  return (
    <button
      className={`inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-50 disabled:pointer-events-none select-none ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin text-current" />
      ) : icon ? (
        <span className="mr-2 inline-flex">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};
