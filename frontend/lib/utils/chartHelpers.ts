import { Candle, SupportResistance } from '@/lib/api/types';

type LineDataPoint = {
  time: number;
  value: number;
};

type CandleDataPoint = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

export function mapCandlesToSeries(candles: Candle[]): CandleDataPoint[] {
  return candles.map((candle) => ({
    time: candle.timestamp / 1000,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close
  }));
}

export function mapIndicatorToSeries(candles: Candle[], values: number[]): LineDataPoint[] {
  return candles.map((candle, index) => ({
    time: candle.timestamp / 1000,
    value: values[index] ?? values[values.length - 1] ?? 0
  }));
}

export function buildPriceLines(levels: SupportResistance[]) {
  return levels.map((level) => ({
    price: level.price,
    title: `${level.strength === 'strong' ? 'Fuerte' : 'Medio'} · ${level.touches}x`
  }));
}
