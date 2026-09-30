import { createContext, useContext, useEffect, useRef, useState } from 'react';

import {
  ApiError,
  getCurrentUser,
  loginUser,
  logoutAllSessions,
  logoutSession,
  refreshTokens,
  registerUser,
} from './api';
import {
  clearRefreshToken,
  getRefreshToken,
  saveRefreshToken,
} from './tokenStorage';
import type { LoginInput, RegistrationInput, Session, TokenPair, User } from './types';

type AuthContextValue = {
  isBootstrapping: boolean;
  restoreError: string | null;
  session: Session | null;
  retryRestore: () => Promise<void>;
  signIn: (input: LoginInput) => Promise<void>;
  signOut: () => Promise<void>;
  signOutAll: () => Promise<void>;
  signUp: (input: RegistrationInput) => Promise<void>;
  refreshProfile: () => Promise<void>;
  withAccessToken: <T>(operation: (accessToken: string) => Promise<T>) => Promise<T>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const sessionRef = useRef<Session | null>(null);
  const refreshPromiseRef = useRef<Promise<Session> | null>(null);

  function updateSession(nextSession: Session | null) {
    sessionRef.current = nextSession;
    setSession(nextSession);
  }

  async function rotateSession(existingUser?: User): Promise<Session> {
    if (refreshPromiseRef.current) return refreshPromiseRef.current;

    const rotation = (async () => {
      const storedRefreshToken = await getRefreshToken();
      if (!storedRefreshToken) throw new ApiError('No hay una sesión para renovar.', 401);

      const tokenPair = await refreshTokens(storedRefreshToken);
      await saveRefreshToken(tokenPair.refresh_token);
      const user = existingUser ?? await getCurrentUser(tokenPair.access_token);
      const nextSession = toSession(tokenPair, user);
      updateSession(nextSession);
      return nextSession;
    })();

    refreshPromiseRef.current = rotation;
    try {
      return await rotation;
    } finally {
      refreshPromiseRef.current = null;
    }
  }

  async function restoreSession() {
    setIsBootstrapping(true);
    setRestoreError(null);
    const result = await readStoredSession();
    updateSession(result.session);
    setRestoreError(result.error);
    setIsBootstrapping(false);
  }

  useEffect(() => {
    let active = true;
    void readStoredSession().then((result) => {
      if (!active) return;
      sessionRef.current = result.session;
      setSession(result.session);
      setRestoreError(result.error);
      setIsBootstrapping(false);
    });
    return () => {
      active = false;
    };
  }, []);

  async function signIn(input: LoginInput) {
    const tokenPair = await loginUser(input);
    await saveRefreshToken(tokenPair.refresh_token);
    const user = await getCurrentUser(tokenPair.access_token);
    updateSession(toSession(tokenPair, user));
    setRestoreError(null);
  }

  async function signUp(input: RegistrationInput) {
    await registerUser(input);
    await signIn({ email: input.email, password: input.password });
  }

  async function withAccessToken<T>(operation: (accessToken: string) => Promise<T>): Promise<T> {
    const currentSession = sessionRef.current;
    if (!currentSession) throw new ApiError('Debes iniciar sesión.', 401);

    try {
      return await operation(currentSession.accessToken);
    } catch (error) {
      if (!(error instanceof ApiError) || error.statusCode !== 401) throw error;
      const renewed = await rotateSession(currentSession.user);
      return operation(renewed.accessToken);
    }
  }

  async function refreshProfile() {
    const user = await withAccessToken(getCurrentUser);
    const currentSession = sessionRef.current;
    if (currentSession) updateSession({ ...currentSession, user });
  }

  async function signOut() {
    const storedRefreshToken = await getRefreshToken();
    try {
      if (storedRefreshToken) await logoutSession(storedRefreshToken);
    } finally {
      await clearRefreshToken();
      updateSession(null);
    }
  }

  async function signOutAll() {
    try {
      await withAccessToken(logoutAllSessions);
    } finally {
      await clearRefreshToken();
      updateSession(null);
    }
  }

  const value: AuthContextValue = {
    isBootstrapping,
    restoreError,
    session,
    retryRestore: restoreSession,
    signIn,
    signOut,
    signOutAll,
    signUp,
    refreshProfile,
    withAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}

function toSession(tokenPair: TokenPair, user: User): Session {
  return {
    accessToken: tokenPair.access_token,
    accessExpiresAt: tokenPair.access_expires_at,
    refreshExpiresAt: tokenPair.refresh_expires_at,
    user,
  };
}

async function readStoredSession(): Promise<{ session: Session | null; error: string | null }> {
  const storedRefreshToken = await getRefreshToken();
  if (!storedRefreshToken) return { session: null, error: null };

  try {
    const tokenPair = await refreshTokens(storedRefreshToken);
    await saveRefreshToken(tokenPair.refresh_token);
    const user = await getCurrentUser(tokenPair.access_token);
    return { session: toSession(tokenPair, user), error: null };
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 401) {
      await clearRefreshToken();
      return { session: null, error: null };
    }
    return {
      session: null,
      error: 'No pudimos restaurar tu sesión. Puedes reintentar o iniciar sesión otra vez.',
    };
  }
}
