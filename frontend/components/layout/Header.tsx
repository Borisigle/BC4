'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Menu, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils/formatters';

const navigation = [
  { name: 'Overview', href: '/' },
  { name: 'BTC', href: '/btc' },
  { name: 'ETH', href: '/eth' },
  { name: 'SOL', href: '/sol' }
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-gray-900/80 bg-[#0f1116]/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 lg:px-8">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-6 w-6 text-blue-500" />
          <div>
            <p className="text-sm uppercase tracking-widest text-gray-500">Crypto Signal Dashboard</p>
            <h2 className="text-lg font-semibold text-white">Panel de Control</h2>
          </div>
        </div>

        <nav className="hidden items-center gap-2 rounded-full border border-gray-800 bg-gray-900/60 p-1 text-sm font-medium text-gray-400 md:flex">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'rounded-full px-4 py-1.5 transition-colors',
                pathname === item.href ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'hover:text-gray-100'
              )}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3 text-sm text-gray-400">
          <TrendingUp className="hidden h-5 w-5 text-emerald-400 sm:block" />
          <span className="hidden sm:block">Mercados en vivo</span>
          <button className="inline-flex items-center justify-center rounded-full border border-gray-800 p-2 text-gray-400 md:hidden">
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
