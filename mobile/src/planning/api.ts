import { request } from '../auth/api.ts';

export type PlanningKind = 'income' | 'commitments';
export type PlanningInput = {
  description: string;
  amount: string;
  currency: 'ARS' | 'USD';
  recurrence: 'ONE_TIME' | 'MONTHLY';
  preferred_account_id?: string | null;
} & ({ expected_date: string } | { due_date: string });
export type PlanningRecord = PlanningInput & {
  id: string;
  status: 'PLANNED' | 'RECEIVED' | 'PAID' | 'CANCELLED';
  account_id: string | null;
  confirmed_at: string | null;
  already_in_balance: boolean | null;
  remember_account: boolean;
  preferred_account_name?: string | null;
  created_at: string;
  template_id: string | null;
};

export function confirmPlanningRecord(
  token: string, kind: PlanningKind, id: string,
  accountId: string, alreadyInBalance: boolean, rememberAccount = false,
): Promise<PlanningRecord> {
  return request<PlanningRecord>(`/api/v1/${kind}/${encodeURIComponent(id)}/confirm`, {
    accessToken: token, method: 'POST',
    body: { account_id: accountId, already_in_balance: alreadyInBalance, ...(rememberAccount ? { remember_account: true } : {}) },
  });
}

export function createPlanningRecord(token: string, kind: PlanningKind, input: PlanningInput): Promise<PlanningRecord> {
  return request<PlanningRecord>(`/api/v1/${kind}`, { accessToken: token, method: 'POST', body: input });
}

export function listPlanningRecords(token: string, kind: PlanningKind, year: string, month: string, offset = 0): Promise<PlanningRecord[]> {
  return request<PlanningRecord[]>(`/api/v1/${kind}?year=${year}&month=${month}&include_overdue=true&limit=21&offset=${offset}`, { accessToken: token });
}

export function stopMonthlyPlan(token: string, templateId: string, fromMonth: string): Promise<{ id: string; stopped_from: string | null }> {
  return request(`/api/v1/monthly-plans/${encodeURIComponent(templateId)}/stop`, { accessToken: token, method: 'POST', body: { from_month: fromMonth } });
}

export function editMonthlyPlan(token: string, templateId: string, amount: string, firstDate: string): Promise<{ id: string; stopped_from: string | null }> {
  return request(`/api/v1/monthly-plans/${encodeURIComponent(templateId)}/edit`, { accessToken: token, method: 'POST', body: { amount, first_date: firstDate } });
}

export type CorrectionResult = { id: string; already_in_balance: boolean; corrected_at: string; balance_before: string | null; balance_after: string | null };
export function correctPlanningRecord(token: string, kind: PlanningKind, record: PlanningRecord): Promise<CorrectionResult> {
  return request(`/api/v1/${kind}/${encodeURIComponent(record.id)}/correct`, { accessToken: token, method: 'POST', body: { original_confirmed_at: record.confirmed_at } });
}
