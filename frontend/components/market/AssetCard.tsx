import type { ReactNode } from 'react';
import Link from 'next/link';
import { ArrowUpRight, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import TrendBadge from '@/components/market/TrendBadge';
import { Asset } from '@/lib/api/types';
import { cn, formatPercentage, formatPrice, percentageColor } from '@/lib/utils/formatters';

interface AssetCardProps {
  asset: Asset;
}

function resolveRoute(symbol: string) {
  const base = symbol.split('/')[0]?.toLowerCase();
  if (!base) return '#';
  return `/${base}`;
}

export default function AssetCard({ asset }: AssetCardProps) {
  const route = resolveRoute(asset.symbol);
  const changeColor = percentageColor(asset.change_24h);

  return (
    <Link href={route} className="group block">
      <Card className="h-full transition-transform group-hover:-translate-y-1 group-hover:border-blue-500/40 group-hover:shadow-blue-500/10">
        <CardHeader className="mb-3 flex flex-row items-start justify-between">
          <div>
            <CardTitle>{asset.symbol}</CardTitle>
            <p className="text-sm text-gray-400">Precio actual</p>
          </div>
          <TrendBadge trend={asset.trend_4h} timeframeLabel="4H" />
        </CardHeader>
        <CardContent className="gap-6">
          <div>
            <p className="text-2xl font-semibold text-white">{formatPrice(asset.price)}</p>
            <p className={cn('mt-1 text-sm font-medium', changeColor)}>
              {formatPercentage(asset.change_24h)} en 24h
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <IndicatorBlock label="ADX" value={asset.adx.toFixed(1)}>
              <TrendingUp className="h-4 w-4 text-blue-400" />
            </IndicatorBlock>
            <IndicatorBlock label="RSI" value={asset.rsi.toFixed(1)}>
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </IndicatorBlock>
            <IndicatorBlock label="ATR" value={asset.atr.toFixed(2)}>
              <TrendingUp className="h-4 w-4 text-amber-400" />
            </IndicatorBlock>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <MovingAverage label="EMA 20" value={asset.ema_20} />
            <MovingAverage label="EMA 50" value={asset.ema_50} />
          </div>
        </CardContent>
        <CardFooter className="mt-3 flex items-center justify-between text-xs text-gray-400">
          <span>Tendencia 1H: {asset.trend_1h}</span>
          <span className="inline-flex items-center gap-1 text-blue-400">
            Ver detalles
            <ArrowUpRight className="h-3 w-3" />
          </span>
        </CardFooter>
      </Card>
    </Link>
  );
}

interface IndicatorBlockProps {
  label: string;
  value: string;
  children: React.ReactNode;
}

function IndicatorBlock({ label, value, children }: IndicatorBlockProps) {
  return (
    <div className="rounded-lg border border-gray-800/80 bg-gray-900/60 p-2 text-center">
      <div className="flex items-center justify-center gap-1 text-gray-400">
        {children}
        <span>{label}</span>
      </div>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

interface MovingAverageProps {
  label: string;
  value: number;
}

function MovingAverage({ label, value }: MovingAverageProps) {
  return (
    <div className="rounded-lg border border-gray-800/80 bg-gray-900/40 p-2 text-center">
      <p className="text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-white">{formatPrice(value)}</p>
    </div>
  );
}
