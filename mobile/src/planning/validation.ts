import type { PlanningInput, PlanningKind, PlanningRecord } from './api.ts';

const financialDateFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/Argentina/Cordoba', year: 'numeric', month: '2-digit', day: '2-digit',
});

export function financialDate(now = new Date()): string {
  const parts = financialDateFormatter.formatToParts(now);
  const part = (name: string) => parts.find((value) => value.type === name)!.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

export function validFinancialDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000')) return false;
  const parsed = new Date(`${value}T12:00:00Z`);
  return !isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function normalizePlanningDate(value: string): string {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value.trim());
  return match ? `${match[3]}-${match[2]}-${match[1]}` : value.trim();
}

export function monthAtOffset(today: string, offset: number): string {
  const [year, month] = today.split('-');
  const index = parseInt(year, 10) * 12 + parseInt(month, 10) - 1 + offset;
  return `${Math.floor(index / 12).toString().padStart(4, '0')}-${(index % 12 + 1).toString().padStart(2, '0')}`;
}

export function validatePlanningInput(kind: PlanningKind, description: string, amount: string, currency: string, date: string, recurrence: string = 'ONE_TIME'): { input: PlanningInput; error?: never } | { error: string; input?: never } {
  const normalizedAmount = amount.trim().replace(',', '.');
  if (!description.trim() || description.trim().length > 100) return { error: 'Ingresá una descripción de hasta 100 caracteres.' };
  if (!/^(?:0|[1-9]\d{0,17})(?:\.\d{1,2})?$/.test(normalizedAmount) || !/[1-9]/.test(normalizedAmount)) {
    return { error: 'Ingresá un importe mayor que cero, con hasta 18 enteros y 2 decimales, sin separadores de miles.' };
  }
  if (currency !== 'ARS' && currency !== 'USD') return { error: 'Elegí ARS o USD.' };
  const normalizedDate = normalizePlanningDate(date);
  if (!validFinancialDate(normalizedDate)) return { error: 'Ingresá una fecha válida como DD/MM/AAAA, por ejemplo 15/10/2026.' };
  if (recurrence !== 'ONE_TIME' && recurrence !== 'MONTHLY') return { error: 'Elegí una vez o todos los meses.' };
  return { input: { description: description.trim(), amount: normalizedAmount, currency, recurrence, ...(kind === 'income' ? { expected_date: normalizedDate } : { due_date: normalizedDate }) } };
}

export function recordDate(record: PlanningRecord): string {
  return 'expected_date' in record ? record.expected_date : record.due_date;
}

export function displayFinancialDate(date: string): string {
  const [year, month, day] = date.split('-');
  return `${day}/${month}/${year}`;
}
