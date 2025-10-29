import { ArrowRight } from 'lucide-react';
import AssetCard from '@/components/market/AssetCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import TrendBadge from '@/components/market/TrendBadge';
import { MarketOverview as MarketOverviewType } from '@/lib/api/types';
import { formatDateTime } from '@/lib/utils/formatters';

interface MarketOverviewProps {
  data: MarketOverviewType;
}

export default function MarketOverview({ data }: MarketOverviewProps) {
  const topAssets = data.assets.slice(0, 3);
  const restAssets = data.assets.slice(3);

  return (
    <section className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl text-white">
              Contexto de Mercado
              <ArrowRight className="h-4 w-4 text-blue-500" />
            </CardTitle>
            <p className="text-sm text-gray-400">Resumen del estado actual del mercado y activos monitoreados.</p>
          </div>
          <TrendBadge trend={data.btc_context.trend} timeframeLabel="BTC" />
        </CardHeader>
        <CardContent className="space-y-0 grid gap-4 lg:grid-cols-4">
          <div className="rounded-xl border border-gray-800/80 bg-gray-900/60 p-4">
            <p className="text-xs uppercase tracking-wide text-gray-400">Última actualización</p>
            <p className="text-lg font-semibold text-white">{formatDateTime(data.timestamp)}</p>
            <p className="mt-2 text-sm text-gray-400">
              Sesión: <span className="font-semibold text-gray-200">{data.btc_context.session_quality}</span>
            </p>
            <p className="text-sm text-gray-400">
              Volatilidad: <span className="font-semibold text-gray-200">{data.btc_context.volatility}</span>
            </p>
          </div>
          {topAssets.map((asset) => (
            <AssetCard key={asset.symbol} asset={asset} />
          ))}
        </CardContent>
      </Card>

      {restAssets.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {restAssets.map((asset) => (
            <AssetCard key={asset.symbol} asset={asset} />
          ))}
        </div>
      )}
    </section>
  );
}
