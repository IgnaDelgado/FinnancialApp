# Financial Plan mobile client

Expo SDK 57 and React Native client for authentication and manual financial accounts.

## What is implemented

- Registration with ARS or USD as the reference currency.
- Login and authenticated profile retrieval.
- Short-lived access tokens kept only in memory.
- Rotating refresh tokens stored with Expo SecureStore on native devices.
- Session restoration when the native application starts.
- Logout for the current device or every refresh session.
- Development web preview sessions survive F5 in the same tab through `sessionStorage`; production web does not persist refresh tokens until a secure-cookie design is approved.
- Expo Router public and authenticated route groups.
- Registration feedback for invalid email, password length, confirmation, and duplicate email.
- Account creation and balance updates, including negative balances.
- Bottom navigation for Accounts, Month, Goals, Investments, and Profile.
- Accounts shows a five-account preview, pages of 50 for management, and per-currency totals across all active accounts. Profile holds user details and logout separately.
- Tu mes creates one-time planned income and commitments with description,
  positive ARS/USD amount, and financial date. It shows the current month and
  all older pending records in separate lists with pages of 20, overdue labels,
  loading, errors, retry, and refresh. Money remains decimal strings.
- Past and future dates are accepted. Future-month entries appear when that
  month arrives; confirmation explains this. Financial dates use Argentina.
- Registering an expected event does not change account balances or snapshots.
  Received/paid states and record modifications remain for a later slice.
- Goals and Investments remain clearly marked as coming soon.

Budgets, goals, investments, net worth, and safe-to-spend calculations belong to later roadmap milestones. The Accounts tab shows only recorded account cash and labels it separately from those future calculations.

## Configure the backend URL

Expo exposes variables prefixed with `EXPO_PUBLIC_` to application code. They
are public bundle configuration and must never contain secrets.

Copy `.env.example` to the ignored `.env.local` and replace the address:

```powershell
Copy-Item .env.example .env.local
```

- The iPhone must use the computer's LAN IP, such as
  `http://192.168.1.100:8000`.
- Web on the same computer can use `http://localhost:8000`.
- Production must use the deployed API's HTTPS URL.

`EXPO_PUBLIC_API_URL` is required. Restart Expo after changing it so the new
value is included in the application bundle.

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
npm test
npx expo-doctor
```

## Source map

- `src/app/`: file-based routes and layouts.
- `src/auth/api.ts`: HTTP requests and API error translation.
- `src/auth/registrationValidation.ts`: immediate registration-field feedback.
- `src/auth/AuthProvider.tsx`: session lifecycle and token rotation.
- `src/auth/tokenStorage.native.ts`: encrypted native refresh-token storage.
- `src/components/`: reusable presentation components.
- `src/theme.ts`: shared design tokens.
- `src/planning/`: one-time planning API, validation, and forms/lists.

The detailed learning guide is in `docs/mobile-authentication-course.md`.
