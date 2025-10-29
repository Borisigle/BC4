'use client';

import * as React from 'react';
import { cn } from '@/lib/utils/formatters';

const variants = {
  default: 'bg-gray-800 text-gray-100',
  success: 'bg-emerald-500/20 text-emerald-300',
  warning: 'bg-yellow-500/20 text-yellow-300',
  danger: 'bg-red-500/20 text-red-300',
  info: 'bg-blue-500/20 text-blue-200',
  outline: 'border border-gray-700 text-gray-300'
} as const;

type VariantKey = keyof typeof variants;

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: VariantKey;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide',
        variants[variant],
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = 'Badge';

export { Badge };
