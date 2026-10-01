const REFRESH_TOKEN_KEY = 'financial-plan.preview-refresh-token';
let memoryRefreshToken: string | null = null;

function previewStorage(): Storage | null {
  if (process.env.NODE_ENV === 'production' || typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export async function getRefreshToken(): Promise<string | null> {
  try {
    return previewStorage()?.getItem(REFRESH_TOKEN_KEY) ?? memoryRefreshToken;
  } catch {
    return memoryRefreshToken;
  }
}

export async function saveRefreshToken(token: string): Promise<void> {
  memoryRefreshToken = token;
  try {
    previewStorage()?.setItem(REFRESH_TOKEN_KEY, token);
  } catch {
    // The preview still works for this page when browser storage is unavailable.
  }
}

export async function clearRefreshToken(): Promise<void> {
  memoryRefreshToken = null;
  try {
    previewStorage()?.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Clearing the in-memory token still signs out of this page.
  }
}
