import { cn } from '@/lib/utils/formatters';

interface IndicatorBarProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  color?: 'emerald' | 'yellow' | 'red' | 'blue';
  helperText?: string;
}

const colorMap: Record<NonNullable<IndicatorBarProps['color']>, string> = {
  emerald: 'bg-emerald-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500'
};

export default function IndicatorBar({
  label,
  value,
  min = 0,
  max = 100,
  color = 'blue',
  helperText
}: IndicatorBarProps) {
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const barColor = colorMap[color] ?? colorMap.blue;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{label}</span>
        <span className="font-semibold text-white">{value.toFixed(2)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-800">
        <div className={cn('h-full rounded-full transition-all', barColor)} style={{ width: `${percentage}%` }} />
      </div>
      {helperText && <p className="text-[11px] text-gray-500">{helperText}</p>}
    </div>
  );
}
