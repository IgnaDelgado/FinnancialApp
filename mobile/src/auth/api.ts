import type { LoginInput, RegistrationInput, TokenPair, User } from './types';

export class ApiError extends Error {
  readonly statusCode: number | null;

  constructor(
    message: string,
    statusCode: number | null,
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

export function registerUser(input: RegistrationInput): Promise<User> {
  return request<User>('/api/v1/auth/register', { method: 'POST', body: input });
}

export function loginUser(input: LoginInput): Promise<TokenPair> {
  return request<TokenPair>('/api/v1/auth/login', { method: 'POST', body: input });
}

export function getCurrentUser(accessToken: string): Promise<User> {
  return request<User>('/api/v1/auth/me', { accessToken });
}

export function refreshTokens(refreshToken: string): Promise<TokenPair> {
  return request<TokenPair>('/api/v1/auth/refresh', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  });
}

export function logoutSession(refreshToken: string): Promise<void> {
  return request<void>('/api/v1/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  });
}

export function logoutAllSessions(accessToken: string): Promise<void> {
  return request<void>('/api/v1/auth/logout-all', { method: 'POST', accessToken });
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: object;
  accessToken?: string;
};

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body) headers['Content-Type'] = 'application/json';
  if (options.accessToken) headers.Authorization = `Bearer ${options.accessToken}`;

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(
      'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo otra vez.',
      null,
    );
  }

  const responseBody = await readResponseBody(response);
  if (!response.ok) {
    throw new ApiError(errorMessageFor(response.status, responseBody, path), response.status);
  }
  if (response.status === 204) return undefined as T;
  return responseBody as T;
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function errorMessageFor(status: number, body: unknown, path: string): string {
  if (status === 404 && (path.startsWith('/api/v1/home') || path.startsWith('/api/v1/income') || path.startsWith('/api/v1/commitments'))) {
    return 'El servidor no tiene habilitada esta función. Actualizá el backend y volvé a intentar.';
  }
  if (status === 401) return 'El correo, la contraseña o la sesión no son válidos.';
  if (status === 409 && path === '/api/v1/auth/register') {
    return 'Ya existe una cuenta con ese correo. Iniciá sesión o usá otro correo.';
  }
  if (status === 422) return validationMessage(body, path);
  if (status >= 500) return 'El servidor tuvo un problema. Inténtalo nuevamente en unos minutos.';
  return readDetail(body) ?? 'El servidor rechazó la solicitud.';
}

function validationMessage(body: unknown, path: string): string {
  if (typeof body !== 'object' || body === null || !('detail' in body)) {
    return 'Revisa los datos ingresados.';
  }
  const detail = body.detail;
  if (!Array.isArray(detail)) return 'Revisa los datos ingresados.';
  const fieldHasError = (field: string) => detail.some((entry) =>
    typeof entry === 'object' && entry !== null && 'loc' in entry &&
    Array.isArray(entry.loc) && entry.loc.includes(field),
  );
  if (fieldHasError('email')) return 'Ingresá un correo válido, por ejemplo nombre@correo.com.';
  if (fieldHasError('password') && path === '/api/v1/auth/register') {
    return 'La contraseña debe tener entre 8 y 128 caracteres.';
  }
  if (fieldHasError('reference_currency')) return 'Elegí ARS o USD como moneda de referencia.';
  return 'Revisá los datos ingresados.';
}

function readDetail(body: unknown): string | null {
  if (typeof body !== 'object' || body === null || !('detail' in body)) return null;
  return typeof body.detail === 'string' ? body.detail : null;
}

export function getApiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');
  if (configured) return configured;
  throw new ApiError(
    'La aplicación no tiene configurada EXPO_PUBLIC_API_URL.',
    null,
  );
}
