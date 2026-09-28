let refreshToken: string | null = null;

export async function getRefreshToken(): Promise<string | null> {
  return refreshToken;
}

export async function saveRefreshToken(token: string): Promise<void> {
  refreshToken = token;
}

export async function clearRefreshToken(): Promise<void> {
  refreshToken = null;
}
