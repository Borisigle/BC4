import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { Inter } from 'next/font/google';
import clsx from 'clsx';
import '@/styles/globals.css';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Crypto Signal Dashboard',
  description: 'Visualiza la información del bot de señales con gráficos interactivos en tiempo real.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className="h-full">
      <body className={clsx('min-h-screen bg-background text-white antialiased', inter.className)}>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-h-screen flex-1 flex-col">
            <Header />
            <main className="flex-1 overflow-x-hidden bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.08),_transparent_60%)]">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
