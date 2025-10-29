'use client';

import { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { ChartData } from '@/lib/api/types';
import { mapCandlesToSeries, mapIndicatorToSeries } from '@/lib/utils/chartHelpers';

interface TradingViewChartProps {
  data: ChartData;
  height?: number;
}

type LineSeriesType = ISeriesApi<'Line'>;

type CandlestickSeriesType = ISeriesApi<'Candlestick'>;

type SeriesCollection = {
  candles?: CandlestickSeriesType;
  ema20?: LineSeriesType;
  ema50?: LineSeriesType;
  vwap?: LineSeriesType;
  cvd?: LineSeriesType;
};

export default function TradingViewChart({ data, height = 400 }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<SeriesCollection>({});

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height,
      width: container.clientWidth,
      layout: {
        background: { color: '#0f1116' },
        textColor: '#d1d4dc'
      },
      grid: {
        horzLines: { color: '#1f242b' },
        vertLines: { color: '#1f242b' }
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2a2f37'
      },
      rightPriceScale: {
        borderColor: '#2a2f37'
      },
      crosshair: {
        mode: 1
      }
    });

    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#16a34a',
      downColor: '#f87171',
      borderVisible: false,
      wickUpColor: '#16a34a',
      wickDownColor: '#f87171'
    });

    seriesRef.current.candles = candleSeries;

    const ema20Series = chart.addLineSeries({
      color: '#2563eb',
      lineWidth: 2,
      priceLineVisible: false
    });
    seriesRef.current.ema20 = ema20Series;

    const ema50Series = chart.addLineSeries({
      color: '#f97316',
      lineWidth: 2,
      priceLineVisible: false
    });
    seriesRef.current.ema50 = ema50Series;

    const vwapSeries = chart.addLineSeries({
      color: '#a855f7',
      lineWidth: 1,
      priceLineVisible: false,
      lineStyle: 2
    });
    seriesRef.current.vwap = vwapSeries;

    const cvdSeries = chart.addLineSeries({
      color: '#00bcd4',
      lineWidth: 2,
      priceLineVisible: false,
      priceScaleId: 'cvd'
    });
    chart.priceScale('cvd').applyOptions({
      scaleMargins: { top: 0.7, bottom: 0.0 },
      borderVisible: false
    });
    seriesRef.current.cvd = cvdSeries;

    const resizeObserver = new ResizeObserver(() => {
      const { clientWidth } = container;
      chart.applyOptions({ width: clientWidth, height });
      chart.timeScale().fitContent();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = {};
    };
  }, [height]);

  useEffect(() => {
    const chart = chartRef.current;
    const { candles, ema20, ema50, vwap, cvd } = seriesRef.current;
    if (!chart || !candles || !ema20 || !ema50 || !vwap) {
      return;
    }

    const candleData = mapCandlesToSeries(data.candles);
    candles.setData(candleData);
    ema20.setData(mapIndicatorToSeries(data.candles, data.indicators.ema_20));
    ema50.setData(mapIndicatorToSeries(data.candles, data.indicators.ema_50));
    vwap.setData(mapIndicatorToSeries(data.candles, data.indicators.vwap));
    if (cvd) {
      cvd.setData(mapIndicatorToSeries(data.candles, data.indicators.cvd));
    }

    candles.applyOptions({ priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });

    // Clear existing price lines by recreating series price lines
    candles.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0.1 } });

    data.market_structure.resistances.forEach((level) => {
      candles.createPriceLine({
        price: level.price,
        color: '#ef4444',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `R ${level.strength === 'strong' ? 'Fuerte' : 'Media'} (${level.touches}x)`
      });
    });

    data.market_structure.supports.forEach((level) => {
      candles.createPriceLine({
        price: level.price,
        color: '#22c55e',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `S ${level.strength === 'strong' ? 'Fuerte' : 'Media'} (${level.touches}x)`
      });
    });

    chart.timeScale().fitContent();
  }, [data]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
