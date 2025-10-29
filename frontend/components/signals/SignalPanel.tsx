import { Signal } from '@/lib/api/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import SignalCard from '@/components/signals/SignalCard';

interface SignalPanelProps {
  signals: Signal[];
}

export default function SignalPanel({ signals }: SignalPanelProps) {
  return (
    <section>
      <Card>
        <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="text-2xl text-white">Señales en tiempo real</CardTitle>
            <p className="text-sm text-gray-400">
              Entradas más recientes alineadas con el contexto del bot.
            </p>
          </div>
          <span className="text-sm text-gray-400">Actualización automática cada 60s</span>
        </CardHeader>
        <CardContent className="space-y-4">
          {signals.length === 0 && (
            <div className="rounded-xl border border-dashed border-gray-700 bg-gray-900/40 p-6 text-center text-sm text-gray-400">
              No hay señales activas por el momento. Mantente atento a nuevas oportunidades.
            </div>
          )}
          {signals.map((signal) => (
            <SignalCard key={`${signal.symbol}-${signal.timestamp}`} signal={signal} />
          ))}
        </CardContent>
      </Card>
    </section>
  );
}
