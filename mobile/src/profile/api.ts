import { request } from '../auth/api.ts';

export type UserDataExport = { schema_version: number; exported_at: string } & Record<string, unknown>;

export function exportUserData(token: string): Promise<UserDataExport> {
  return request('/api/v1/user-data/export', { accessToken: token });
}

export function deleteUserAccount(token: string, password: string): Promise<void> {
  return request('/api/v1/user-data', { accessToken: token, method: 'DELETE', body: { password } });
}
