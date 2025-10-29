'use client';

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import TradingViewChart from '@/components/charts/TradingViewChart';
import IndicatorPanel from '@/components/indicators/IndicatorPanel';
import StructurePanel from '@/components/structure/StructurePanel';
import { useChartData } from '@/lib/api/hooks';
import { formatPrice } from '@/lib/utils/formatters';

export default function ETHPage() {
  const {
    data: data4h,
    isLoading: loading4h,
    error: error4h
  } = useChartData('ETH/USDT', '4h', 200);
  const {
    data: data1h,
    isLoading: loading1h,
    error: error1h
  } = useChartData('ETH/USDT', '1h', 200);

  if (loading4h || loading1h) {
    return (
      <div className="flex h-[calc(100vh-88px)] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error4h || error1h || !data4h || !data1h) {
    return (
      <div className="flex h-[calc(100vh-88px)] items-center justify-center text-red-500">
        Error al cargar los datos del gráfico. Verifica la API.
      </div>
    );
  }

  const currentPrice = data1h.candles[data1h.candles.length - 1]?.close ?? 0;
  const latestIndicators = {
    adx: data4h.indicators.adx[data4h.indicators.adx.length - 1] ?? 0,
    rsi: data4h.indicators.rsi[data4h.indicators.rsi.length - 1] ?? 0,
    atr: data4h.indicators.atr[data4h.indicators.atr.length - 1] ?? 0
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 lg:px-8">
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-gray-400 transition-colors hover:text-white">
            <ArrowLeft />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white">ETH / USDT</h1>
            <p className="text-2xl font-semibold text-emerald-400">{formatPrice(currentPrice)}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-gray-400">Tendencia 4H</p>
          <p className="text-xl font-semibold text-yellow-400">{data4h.trend.current}</p>
          {data4h.trend.signal && (
            <p className="text-sm text-gray-400">{data4h.trend.signal}</p>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-4 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Gráfico 4H (Estructura)</h2>
              <span className="text-xs text-gray-400">Última vela: {data4h.candles[data4h.candles.length - 1]?.datetime ?? ''}</span>
            </div>
            <TradingViewChart data={data4h} height={420} />
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-4 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Gráfico 1H (Confirmación)</h2>
              <span className="text-xs text-gray-400">Última vela: {data1h.candles[data1h.candles.length - 1]?.datetime ?? ''}</span>
            </div>
            <TradingViewChart data={data1h} height={320} />
          </div>
        </div>

        <div className="space-y-6">
          <IndicatorPanel indicators={latestIndicators} timeframe="4H" />
          <StructurePanel data={data4h.market_structure} trend={data4h.trend} />
        </div>
      </div>
    </div>
  );
}
