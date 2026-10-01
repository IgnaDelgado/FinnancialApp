import { request } from '@/auth/api';

export type AccountType =
  | 'CASH'
  | 'BANK'
  | 'DIGITAL_WALLET'
  | 'FOREIGN_CURRENCY'
  | 'INVESTMENT'
  | 'OTHER';

export type Currency = 'ARS' | 'USD';

export type FinancialAccount = {
  id: string;
  name: string;
  account_type: AccountType;
  currency: Currency;
  current_balance: string;
  is_liquid: boolean;
  balance_updated_at: string;
  archived_at: string | null;
  created_at: string;
};

export type AccountCashTotal = {
  currency: Currency;
  balance: string;
};

export type CreateAccountInput = {
  name: string;
  account_type: AccountType;
  currency: Currency;
  initial_balance: string;
  is_liquid: boolean;
};

export function listAccounts(
  accessToken: string,
  { limit = 50, offset = 0 }: { limit?: number; offset?: number } = {},
): Promise<FinancialAccount[]> {
  return request<FinancialAccount[]>(`/api/v1/accounts?limit=${limit}&offset=${offset}`, { accessToken });
}

export function getAccountCashTotals(accessToken: string): Promise<AccountCashTotal[]> {
  return request<AccountCashTotal[]>('/api/v1/accounts/totals', { accessToken });
}

export function createAccount(
  accessToken: string,
  input: CreateAccountInput,
): Promise<FinancialAccount> {
  return request<FinancialAccount>('/api/v1/accounts', {
    method: 'POST',
    body: input,
    accessToken,
  });
}

export function getAccount(accessToken: string, accountId: string): Promise<FinancialAccount> {
  return request<FinancialAccount>(`/api/v1/accounts/${accountId}`, { accessToken });
}

export function updateAccountBalance(
  accessToken: string,
  accountId: string,
  balance: string,
): Promise<FinancialAccount> {
  return request<FinancialAccount>(`/api/v1/accounts/${accountId}/balance`, {
    method: 'PATCH',
    body: { balance },
    accessToken,
  });
}

export function archiveAccount(accessToken: string, accountId: string): Promise<void> {
  return request<void>(`/api/v1/accounts/${accountId}`, {
    method: 'DELETE',
    accessToken,
  });
}
