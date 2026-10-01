import type { PlanningInput, PlanningKind, PlanningRecord } from './api.ts';

export function financialDate(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Argentina/Cordoba', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const part = (name: string) => parts.find((value) => value.type === name)!.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

export function validFinancialDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000')) return false;
  const parsed = new Date(`${value}T12:00:00Z`);
  return !isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function validatePlanningInput(kind: PlanningKind, description: string, amount: string, currency: string, date: string): { input: PlanningInput; error?: never } | { error: string; input?: never } {
  const normalizedAmount = amount.trim().replace(',', '.');
  if (!description.trim() || description.trim().length > 100) return { error: 'Ingresá una descripción de hasta 100 caracteres.' };
  if (!/^(?:0|[1-9]\d{0,17})(?:\.\d{1,2})?$/.test(normalizedAmount) || !/[1-9]/.test(normalizedAmount)) {
    return { error: 'Ingresá un importe mayor que cero, con hasta 18 enteros y 2 decimales, sin separadores de miles.' };
  }
  if (currency !== 'ARS' && currency !== 'USD') return { error: 'Elegí ARS o USD.' };
  if (!validFinancialDate(date)) return { error: 'Ingresá una fecha válida como AAAA-MM-DD, por ejemplo 2026-10-15.' };
  return { input: { description: description.trim(), amount: normalizedAmount, currency, recurrence: 'ONE_TIME', ...(kind === 'income' ? { expected_date: date } : { due_date: date }) } };
}

export function recordDate(record: PlanningRecord): string {
  return 'expected_date' in record ? record.expected_date : record.due_date;
}

export function displayFinancialDate(date: string): string {
  const [year, month, day] = date.split('-');
  return `${day}/${month}/${year}`;
}
