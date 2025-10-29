import { SupportResistance } from '@/lib/api/types';
import { formatPrice } from '@/lib/utils/formatters';

interface SupportResistanceListProps {
  title: string;
  levels: SupportResistance[];
  tone: 'support' | 'resistance';
}

export default function SupportResistanceList({ title, levels, tone }: SupportResistanceListProps) {
  const color = tone === 'support' ? 'text-emerald-300' : 'text-red-300';

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-300">{title}</h4>
      <div className="mt-2 space-y-2">
        {levels.length === 0 && <p className="text-xs text-gray-500">Sin niveles detectados</p>}
        {levels.map((level, index) => (
          <div
            key={`${tone}-${level.price}-${index}`}
            className="flex items-center justify-between rounded-lg border border-gray-800/60 bg-gray-900/40 px-3 py-2 text-xs"
          >
            <div>
              <p className="font-semibold text-white">{formatPrice(level.price)}</p>
              <p className="text-[11px] text-gray-500">Toques: {level.touches}</p>
            </div>
            <span className={color}>{level.strength === 'strong' ? 'Fuerte' : 'Media'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
