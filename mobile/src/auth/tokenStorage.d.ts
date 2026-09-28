export function getRefreshToken(): Promise<string | null>;
export function saveRefreshToken(token: string): Promise<void>;
export function clearRefreshToken(): Promise<void>;
