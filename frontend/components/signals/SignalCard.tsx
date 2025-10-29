import { ArrowUpCircle, ArrowDownCircle, Clock, Gauge } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Signal } from '@/lib/api/types';
import { cn, formatDateTime, formatPercentage, formatPrice } from '@/lib/utils/formatters';

interface SignalCardProps {
  signal: Signal;
}

export default function SignalCard({ signal }: SignalCardProps) {
  const isLong = signal.direction === 'LONG';
  const DirectionIcon = isLong ? ArrowUpCircle : ArrowDownCircle;

  return (
    <Card className={cn('h-full border-l-4', isLong ? 'border-l-emerald-500/60' : 'border-l-red-500/60')}>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-xl">
            {signal.symbol}
            <Badge variant={isLong ? 'success' : 'danger'}>{signal.direction}</Badge>
          </CardTitle>
          <p className="text-sm text-gray-400">Score: {signal.score.toFixed(1)} · Confianza: {signal.confidence}</p>
        </div>
        <DirectionIcon className={cn('h-6 w-6', isLong ? 'text-emerald-400' : 'text-red-400')} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-xs text-gray-400">
          <div>
            <p className="text-gray-400">Entrada</p>
            <p className="text-sm font-semibold text-white">{formatPrice(signal.entry_price)}</p>
          </div>
          <div>
            <p className="text-gray-400">Stop Loss</p>
            <p className="text-sm font-semibold text-white">{formatPrice(signal.stop_loss)}</p>
          </div>
          <div>
            <p className="text-gray-400">Take Profit 1</p>
            <p className="text-sm font-semibold text-white">{formatPrice(signal.take_profit_1)}</p>
          </div>
          <div>
            <p className="text-gray-400">Take Profit 2</p>
            <p className="text-sm font-semibold text-white">{formatPrice(signal.take_profit_2)}</p>
          </div>
          <div>
            <p className="text-gray-400">Take Profit 3</p>
            <p className="text-sm font-semibold text-white">{formatPrice(signal.take_profit_3)}</p>
          </div>
          <div>
            <p className="text-gray-400">Riesgo</p>
            <p className="text-sm font-semibold text-white">{formatPercentage(signal.risk_percent)}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 text-center text-xs">
          <IndicatorPill label="ATR" value={signal.indicators.atr.toFixed(2)} />
          <IndicatorPill label="ADX" value={signal.indicators.adx.toFixed(1)} />
          <IndicatorPill label="RSI" value={signal.indicators.rsi.toFixed(1)} />
        </div>

        <div className="space-y-2 text-xs">
          <p className="text-sm font-semibold text-gray-300">Razones de la señal</p>
          {signal.reasons.length === 0 && <p className="text-gray-500">Sin detalles adicionales.</p>}
          {signal.reasons.map((reason, index) => (
            <div key={`${signal.symbol}-reason-${index}`} className="flex items-start gap-2 text-gray-300">
              <span className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-400" />
              <span>{reason}</span>
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-2 text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-blue-400" />
          Emitida: {formatDateTime(signal.timestamp)} · Válida hasta: {formatDateTime(signal.valid_until)}
        </div>
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-yellow-300" />
          BTC: {signal.btc_trend} · Sesión: {signal.session_quality} · Tamaño sugerido: {formatPrice(signal.suggested_position_size)}
        </div>
      </CardFooter>
    </Card>
  );
}

function IndicatorPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-800/80 bg-gray-900/50 px-3 py-2 text-gray-300">
      <p>{label}</p>
      <p className="text-sm font-semibold text-white">{value}</p>
    </div>
  );
}
