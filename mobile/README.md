# Financial Plan mobile client

Expo SDK 57 and React Native client for the M1 authentication flow.

## What is implemented

- Registration with ARS or USD as the reference currency.
- Login and authenticated profile retrieval.
- Short-lived access tokens kept only in memory.
- Rotating refresh tokens stored with Expo SecureStore on native devices.
- Session restoration when the native application starts.
- Logout for the current device or every refresh session.
- Expo Router public and authenticated route groups.

Financial accounts, balances, budgets, goals, and investments belong to later
roadmap milestones. The authenticated home intentionally displays no invented
balance.

## Configure the backend URL

Expo exposes variables prefixed with `EXPO_PUBLIC_` to application code. They
are public bundle configuration and must never contain secrets.

Copy `.env.example` to the ignored `.env.local` and replace the address:

```powershell
Copy-Item .env.example .env.local
```

- Android Emulator can use `http://10.0.2.2:8000`.
- iOS Simulator and web can use `http://localhost:8000`.
- A physical phone must use the computer's LAN IP, such as
  `http://192.168.1.100:8000`.
- Production must use the deployed API's HTTPS URL.

When `EXPO_PUBLIC_API_URL` is absent in development, the app uses the emulator
defaults above.

## Run and verify

Start PostgreSQL and FastAPI, then run from `mobile/`:

```powershell
npm install
npx expo start
```

Quality checks:

```powershell
npm run lint
npm run typecheck
npx expo-doctor
```

## Source map

- `src/app/`: file-based routes and layouts.
- `src/auth/api.ts`: HTTP requests and API error translation.
- `src/auth/AuthProvider.tsx`: session lifecycle and token rotation.
- `src/auth/tokenStorage.native.ts`: encrypted native refresh-token storage.
- `src/components/`: reusable presentation components.
- `src/theme.ts`: shared design tokens.

The detailed learning guide is in `docs/mobile-authentication-course.md`.
