import { Badge } from '@/components/ui/badge';

interface TrendBadgeProps {
  trend: string;
  timeframeLabel?: string;
}

function trendVariant(trend: string) {
  if (!trend) return 'outline' as const;
  const normalized = trend.toLowerCase();
  if (normalized.includes('alcista') || normalized.includes('bull')) return 'success' as const;
  if (normalized.includes('bajista') || normalized.includes('bear')) return 'danger' as const;
  if (normalized.includes('lateral')) return 'warning' as const;
  return 'info' as const;
}

function normalizeTrend(trend: string) {
  return trend
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function TrendBadge({ trend, timeframeLabel }: TrendBadgeProps) {
  const variant = trendVariant(trend);
  const label = normalizeTrend(trend);

  return (
    <Badge variant={variant} className="gap-2">
      {timeframeLabel && <span className="text-[10px] uppercase text-gray-300/70">{timeframeLabel}</span>}
      <span>{label}</span>
    </Badge>
  );
}
