import { request } from '../auth/api.ts';

export type CashFlow = {
  currency: 'ARS' | 'USD';
  liquid_cash: string;
  pending_bills: string;
  expected_income: string;
  negative_balances: string;
  overdue_income_count: number;
  cash_after_bills: string;
  forecast_after_bills: string;
};
export type HomeSnapshot = {
  today: string;
  month_end: string;
  account_count: number;
  commitment_count: number;
  currencies: CashFlow[];
};
export function getHomeSnapshot(token: string): Promise<HomeSnapshot> {
  return request<HomeSnapshot>('/api/v1/home', { accessToken: token });
}
