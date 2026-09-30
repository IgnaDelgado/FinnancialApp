import type { Currency } from './api';

export function normalizeMoneyInput(value: string): string | null {
  const normalized = value.trim().replace(',', '.');
  if (!/^(?:0|[1-9]\d{0,17})(?:\.\d{1,2})?$/.test(normalized)) return null;
  return normalized;
}

export function formatMoney(value: string, currency: Currency): string {
  const [whole, fraction = ''] = value.split('.');
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${currency} ${grouped},${fraction.padEnd(2, '0')}`;
}
