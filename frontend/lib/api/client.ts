import { ChartData, MarketOverview, SignalsResponse } from '@/lib/api/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json'
    },
    next: { revalidate: 0 }
  });

  if (!response.ok) {
    throw new Error(`Error al consultar ${url}: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchMarketOverview() {
  const url = `${API_BASE_URL}/api/market/overview`;
  return fetchJson<MarketOverview>(url);
}

export function fetchChartData(symbol: string, timeframe: string, limit = 100) {
  const encodedSymbol = encodeURIComponent(symbol);
  const encodedTimeframe = encodeURIComponent(timeframe);
  const url = `${API_BASE_URL}/api/market/chart/${encodedSymbol}/${encodedTimeframe}?limit=${limit}`;
  return fetchJson<ChartData>(url);
}

export function fetchCurrentSignals() {
  const url = `${API_BASE_URL}/api/signals/current`;
  return fetchJson<SignalsResponse>(url);
}
