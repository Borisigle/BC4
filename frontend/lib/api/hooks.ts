import useSWR from 'swr';
import {
  fetchChartData,
  fetchCurrentSignals,
  fetchMarketOverview
} from '@/lib/api/client';
import { ChartData, MarketOverview, SignalsResponse } from '@/lib/api/types';

export function useMarketOverview(refreshInterval = 60_000) {
  return useSWR<MarketOverview>('market-overview', fetchMarketOverview, {
    refreshInterval,
    revalidateOnFocus: true
  });
}

export function useChartData(symbol: string, timeframe: string, limit = 100) {
  return useSWR<ChartData>(
    ['chart-data', symbol, timeframe, limit],
    () => fetchChartData(symbol, timeframe, limit),
    {
      refreshInterval: 60_000,
      revalidateOnFocus: true
    }
  );
}

export function useCurrentSignals(refreshInterval = 60_000) {
  return useSWR<SignalsResponse>('current-signals', fetchCurrentSignals, {
    refreshInterval,
    revalidateOnFocus: true
  });
}
