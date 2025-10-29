import IndicatorBar from '@/components/indicators/IndicatorBar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface IndicatorPanelProps {
  indicators: {
    adx: number;
    rsi: number;
    atr: number;
  };
  timeframe?: string;
}

function adxHelper(value: number) {
  if (value >= 40) return 'Tendencia muy fuerte';
  if (value >= 25) return 'Tendencia definida';
  if (value >= 20) return 'Tendencia moderada';
  return 'Movimiento lateral';
}

function rsiHelper(value: number) {
  if (value >= 70) return 'Zona de sobrecompra';
  if (value <= 30) return 'Zona de sobreventa';
  return 'Zona neutral';
}

export default function IndicatorPanel({ indicators, timeframe = '4H' }: IndicatorPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>📈 Indicadores Técnicos ({timeframe})</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <IndicatorBar
          label="ADX"
          value={indicators.adx}
          max={60}
          color={indicators.adx >= 25 ? 'emerald' : 'yellow'}
          helperText={adxHelper(indicators.adx)}
        />
        <IndicatorBar
          label="RSI"
          value={indicators.rsi}
          color={indicators.rsi >= 70 ? 'red' : indicators.rsi <= 30 ? 'emerald' : 'blue'}
          helperText={rsiHelper(indicators.rsi)}
        />
        <div>
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>ATR</span>
            <span className="font-semibold text-white">{indicators.atr.toFixed(2)}</span>
          </div>
          <p className="mt-1 text-[11px] text-gray-500">Evalúa la volatilidad promedio de las últimas sesiones.</p>
        </div>
      </CardContent>
    </Card>
  );
}
