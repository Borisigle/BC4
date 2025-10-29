'use client';

import { AlertCircle, TrendingUp } from 'lucide-react';
import MarketOverview from '@/components/market/MarketOverview';
import SignalPanel from '@/components/signals/SignalPanel';
import { useMarketOverview, useCurrentSignals } from '@/lib/api/hooks';

export default function Home() {
  const {
    data: marketData,
    error: marketError,
    isLoading: marketLoading
  } = useMarketOverview();
  const {
    data: signalsData,
    error: signalsError,
    isLoading: signalsLoading
  } = useCurrentSignals();

  if (marketLoading || signalsLoading) {
    return (
      <div className="flex h-[calc(100vh-88px)] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-500" />
          <p className="mt-4 text-sm text-gray-400">Cargando datos del mercado...</p>
        </div>
      </div>
    );
  }

  if (marketError || signalsError || !marketData) {
    return (
      <div className="flex h-[calc(100vh-88px)] items-center justify-center">
        <div className="text-center text-red-500">
          <AlertCircle className="mx-auto mb-4 h-12 w-12" />
          <p className="text-lg font-semibold">Error al cargar datos</p>
          <p className="mt-2 text-sm text-red-300">Verifica que la API esté disponible en http://localhost:8000</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 lg:px-8">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-4xl font-bold text-white">
            <TrendingUp className="text-blue-500" />
            Crypto Signal Scanner
          </h1>
          <p className="mt-2 text-sm text-gray-400">Análisis técnico en tiempo real para BTC, ETH y SOL</p>
        </div>
        <div className="rounded-2xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 px-5 py-3 text-right">
          <p className="text-xs uppercase tracking-wide text-gray-400">Última actualización</p>
          <p className="text-sm font-semibold text-white">
            {new Date(marketData.timestamp).toLocaleString('es-ES', {
              hour12: false
            })}
          </p>
        </div>
      </div>

      <div className="mb-6 rounded-2xl border border-gray-800 bg-gray-900/60 p-6 shadow-lg">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-wide text-gray-400">Filtro Maestro</p>
            <h3 className="text-2xl font-semibold text-white">Estado de BTC</h3>
            <p className="mt-2 text-sm text-gray-300">
              Tendencia: <span className="font-bold text-yellow-400">{marketData.btc_context.trend}</span>
              {' · '}
              Fuerza: {marketData.btc_context.trend_strength.toFixed(1)}
              {' · '}
              Volatilidad: {marketData.btc_context.volatility}
              {' · '}
              Sesión: {marketData.btc_context.session_quality}
            </p>
          </div>
          <div>
            {marketData.btc_context.should_trade ? (
              <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/20 px-4 py-2 text-sm font-semibold text-emerald-300">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                Favorable para operar
              </span>
            ) : (
              <span className="inline-flex items-center gap-2 rounded-xl bg-red-500/20 px-4 py-2 text-sm font-semibold text-red-300">
                <span className="inline-block h-2 w-2 rounded-full bg-red-400 animate-pulse" />
                No favorable en este momento
              </span>
            )}
          </div>
        </div>
      </div>

      <MarketOverview data={marketData} />

      <div className="mt-8">
        <SignalPanel signals={signalsData?.signals ?? []} />
      </div>
    </div>
  );
}
