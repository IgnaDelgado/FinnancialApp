import { normalizeMoneyInput } from '../accounts/format.ts';

function cents(value: string): bigint {
  const negative = value.startsWith('-');
  const [whole, fraction = ''] = (negative ? value.slice(1) : value).split('.');
  const result = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
  return negative ? -result : result;
}

export function previewExpense(margin: string, input: string): string | null {
  const amount = normalizeMoneyInput(input);
  if (!amount || cents(amount) <= 0n) return null;
  const result = cents(margin) - cents(amount);
  const absolute = result < 0n ? -result : result;
  return `${result < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`;
}
