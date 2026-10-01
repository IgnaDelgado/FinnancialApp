# ADR 0003: Mobile authentication client

## Status

Accepted.

## Context

Milestone M1 needs a production-shaped mobile authentication flow rather than a
technical endpoint tester. The client must preserve the backend's rotating
refresh-token rules, keep secrets out of ordinary storage, support future
feature screens, and remain understandable to a developer learning React
Native.

## Decision

- Use Expo SDK 57, React Native, TypeScript strict mode, and Expo Router.
- Keep routes under `mobile/src/app/` and non-route code outside that directory.
- Use a small React context provider for global authentication state. Do not add
  a third-party state library before application state demonstrates a need.
- Keep the access token in memory only.
- Store the native refresh token with Expo SecureStore and replace it after each
  successful rotation.
- Do not persist authentication tokens in AsyncStorage.
- In development web previews only, store the refresh token in per-tab
  `sessionStorage` so an F5 reload can restore the session. The token is removed
  on logout and normally disappears when the tab or browser session closes.
  This storage is accessible to JavaScript and therefore exposed to XSS; it is
  not approved for a production web client. Production web continues to use
  memory only until a separate secure, HttpOnly cookie and CSRF decision.
- Configure the API URL through `EXPO_PUBLIC_API_URL`; no secret may use the
  `EXPO_PUBLIC_` prefix because Expo inlines those values into the client bundle.
- Native Android and iOS requests do not depend on browser CORS. Expo Web may
  use local loopback origins in development; deployed browser origins must be
  listed explicitly through `CORS_ALLOWED_ORIGINS`.
- Centralize HTTP paths, JSON serialization, bearer headers, and API errors in
  the auth API module.
- Deduplicate simultaneous refresh attempts and retry an authenticated request
  at most once after a `401` response.
- Treat route protection as a user-interface boundary only. FastAPI remains the
  authoritative security boundary for every protected resource.

## Consequences

The authentication slice is ready to host later account and planning routes
without moving token logic into screens. Native sessions survive application
restarts; development web previews survive a reload within the same tab, while
access credentials remain short-lived. The client still needs a
real deployed HTTPS API URL for production and account recovery remains a
pending product decision.
