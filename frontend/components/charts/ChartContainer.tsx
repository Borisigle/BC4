'use client';

import { ReactNode } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface ChartContainerProps {
  title: string;
  description?: string;
  timeframes: string[];
  activeTimeframe: string;
  onTimeframeChange: (value: string) => void;
  children: ReactNode;
  actions?: ReactNode;
}

export default function ChartContainer({
  title,
  description,
  timeframes,
  activeTimeframe,
  onTimeframeChange,
  children,
  actions
}: ChartContainerProps) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-4 shadow-lg">
      <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          {description && <p className="text-sm text-gray-400">{description}</p>}
        </div>
        <div className="flex items-center gap-3">
          <Tabs defaultValue={activeTimeframe} value={activeTimeframe} onValueChange={onTimeframeChange}>
            <TabsList>
              {timeframes.map((timeframe) => (
                <TabsTrigger key={timeframe} value={timeframe}>
                  {timeframe}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          {actions}
        </div>
      </div>
      <div className="overflow-hidden rounded-xl border border-gray-800 bg-black/20">
        <Tabs defaultValue={activeTimeframe} value={activeTimeframe} onValueChange={onTimeframeChange}>
          {timeframes.map((timeframe) => (
            <TabsContent key={timeframe} value={timeframe} className="p-0">
              {children}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}
