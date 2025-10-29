import clsx from 'clsx';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

type ClassValue = Parameters<typeof clsx>[0];

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatPrice(value: number, currency: string = 'USD') {
  if (Number.isNaN(value)) {
    return '—';
  }

  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency,
    minimumFractionDigits: value >= 1000 ? 0 : 2,
    maximumFractionDigits: 2
  }).format(value);
}

export function formatPercentage(value: number, fractionDigits = 2) {
  if (Number.isNaN(value)) {
    return '0%';
  }
  const formatted = value.toFixed(fractionDigits);
  return `${formatted}%`;
}

export function percentageColor(value: number) {
  if (value > 0) return 'text-emerald-400';
  if (value < 0) return 'text-red-400';
  return 'text-gray-300';
}

export function formatDateTime(timestamp: string | number | Date) {
  if (!timestamp) return '—';
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  return format(date, "d 'de' MMM, HH:mm", { locale: es });
}

export function formatRelativeTime(timestamp: string | number) {
  if (!timestamp) return '';
  const value = typeof timestamp === 'string' ? Date.parse(timestamp) : timestamp;
  const diff = Date.now() - value;
  const minutes = Math.floor(diff / (1000 * 60));
  if (minutes < 1) return 'Hace instantes';
  if (minutes === 1) return 'Hace 1 minuto';
  if (minutes < 60) return `Hace ${minutes} minutos`;
  const hours = Math.floor(minutes / 60);
  if (hours === 1) return 'Hace 1 hora';
  if (hours < 24) return `Hace ${hours} horas`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Hace 1 día';
  return `Hace ${days} días`;
}
