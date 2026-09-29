export type Currency = 'ARS' | 'USD';

export type User = {
  id: string;
  email: string;
  reference_currency: Currency;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  access_expires_at: string;
  refresh_expires_at: string;
  absolute_expires_at: string;
};

export type Session = {
  accessToken: string;
  accessExpiresAt: string;
  refreshExpiresAt: string;
  user: User;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type RegistrationInput = LoginInput & {
  reference_currency: Currency;
};
