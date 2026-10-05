import { request } from '../auth/api.ts';

export type PlanningKind = 'income' | 'commitments';
export type PlanningInput = {
  description: string;
  amount: string;
  currency: 'ARS' | 'USD';
  recurrence: 'ONE_TIME' | 'MONTHLY';
} & ({ expected_date: string } | { due_date: string });
export type PlanningRecord = PlanningInput & {
  id: string;
  status: 'PLANNED' | 'RECEIVED' | 'PAID';
  account_id: string | null;
  confirmed_at: string | null;
  already_in_balance: boolean | null;
  created_at: string;
  template_id: string | null;
};

export function confirmPlanningRecord(
  token: string, kind: PlanningKind, id: string,
  accountId: string, alreadyInBalance: boolean,
): Promise<PlanningRecord> {
  return request<PlanningRecord>(`/api/v1/${kind}/${encodeURIComponent(id)}/confirm`, {
    accessToken: token, method: 'POST',
    body: { account_id: accountId, already_in_balance: alreadyInBalance },
  });
}

export function createPlanningRecord(token: string, kind: PlanningKind, input: PlanningInput): Promise<PlanningRecord> {
  return request<PlanningRecord>(`/api/v1/${kind}`, { accessToken: token, method: 'POST', body: input });
}

export function listPlanningRecords(token: string, kind: PlanningKind, year: string, month: string, offset = 0): Promise<PlanningRecord[]> {
  return request<PlanningRecord[]>(`/api/v1/${kind}?year=${year}&month=${month}&include_overdue=true&limit=21&offset=${offset}`, { accessToken: token });
}
