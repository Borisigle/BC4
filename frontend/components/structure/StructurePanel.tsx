import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import SupportResistanceList from '@/components/structure/SupportResistanceList';
import { MarketStructure, TrendInfo } from '@/lib/api/types';
import { formatDateTime, formatPrice } from '@/lib/utils/formatters';

interface StructurePanelProps {
  data: MarketStructure;
  trend: TrendInfo;
}

export default function StructurePanel({ data, trend }: StructurePanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Estructura de Mercado</CardTitle>
        <p className="text-sm text-gray-400">Identifica las zonas clave de soporte y resistencia</p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-xl border border-gray-800/60 bg-gray-900/40 p-4">
          <p className="text-xs uppercase tracking-wide text-gray-400">Tendencia actual</p>
          <p className="text-lg font-semibold text-white">{trend.current}</p>
          {trend.comment && <p className="text-sm text-gray-400">{trend.comment}</p>}
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-400">
            <p>Bias: <span className="text-gray-200">{trend.bias ?? '—'}</span></p>
            <p>
              Fuerza:
              <span className="text-gray-200">
                {typeof trend.strength === 'number' ? trend.strength.toFixed(1) : trend.strength ?? '—'}
              </span>
            </p>
            {trend.confidence !== undefined && (
              <p>
                Confianza:
                <span className="text-gray-200">
                  {typeof trend.confidence === 'number'
                    ? trend.confidence.toFixed(1)
                    : trend.confidence ?? '—'}
                </span>
              </p>
            )}
            {trend.signal && <p>Señal: <span className="text-gray-200">{trend.signal}</span></p>}
          </div>
        </div>

        <SupportResistanceList title="Resistencias" levels={data.resistances} tone="resistance" />
        <SupportResistanceList title="Soportes" levels={data.supports} tone="support" />

        <div>
          <h4 className="text-sm font-semibold text-gray-300">Swing Points</h4>
          <div className="mt-2 space-y-2 text-xs text-gray-400">
            {data.swing_highs.slice(0, 3).map((swing, index) => (
              <div
                key={`high-${swing.timestamp}-${index}`}
                className="flex items-center justify-between rounded-lg border border-gray-800/60 bg-gray-900/40 px-3 py-2"
              >
                <span>Máximo {index + 1}</span>
                <span className="text-white">{formatPrice(swing.price)}</span>
                <span>{formatDateTime(swing.timestamp)}</span>
              </div>
            ))}
            {data.swing_lows.slice(0, 3).map((swing, index) => (
              <div
                key={`low-${swing.timestamp}-${index}`}
                className="flex items-center justify-between rounded-lg border border-gray-800/60 bg-gray-900/40 px-3 py-2"
              >
                <span>Mínimo {index + 1}</span>
                <span className="text-white">{formatPrice(swing.price)}</span>
                <span>{formatDateTime(swing.timestamp)}</span>
              </div>
            ))}
            {data.swing_highs.length === 0 && data.swing_lows.length === 0 && (
              <p className="text-xs text-gray-500">Sin swings recientes detectados.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
