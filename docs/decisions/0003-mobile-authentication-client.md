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
- Keep the web preview refresh token in memory only. A future production web
  client requires a separate secure-cookie decision.
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
restarts, while access credentials remain short-lived. The client still needs a
real deployed HTTPS API URL for production and account recovery remains a
pending product decision.
