'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, Compass, LineChart, Star } from 'lucide-react';
import { cn } from '@/lib/utils/formatters';

const links = [
  { name: 'Overview', description: 'Contexto completo', href: '/', icon: Compass },
  { name: 'BTC', description: 'Macroestructura BTC', href: '/btc', icon: LineChart },
  { name: 'ETH', description: 'Visión avanzada ETH', href: '/eth', icon: BarChart3 },
  { name: 'SOL', description: 'Seguimiento SOL', href: '/sol', icon: Star }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 border-r border-gray-900/80 bg-[#0c0e13]/90 px-4 py-8 lg:block">
      <div className="space-y-6">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-gray-500">Panel</p>
          <h2 className="text-2xl font-bold text-white">TradingView Pro</h2>
          <p className="mt-2 text-xs text-gray-500">
            Visualiza señales, estructura y contexto de mercado en un solo lugar.
          </p>
        </div>

        <nav className="space-y-2">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'group flex flex-col gap-1 rounded-xl border border-transparent bg-transparent px-4 py-3 transition-all',
                  isActive
                    ? 'border-blue-500/60 bg-blue-500/10 text-white backdrop-blur'
                    : 'hover:border-blue-500/40 hover:bg-blue-500/5 text-gray-300'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5 text-blue-400" />
                  <span className="text-sm font-semibold">{link.name}</span>
                </div>
                <span className="text-xs text-gray-500 group-hover:text-gray-300">{link.description}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
