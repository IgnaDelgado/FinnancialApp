# ADR 0002: Short-lived JWT access and rotating refresh sessions

## Status

Accepted.

## Context

The mobile client needs short-lived credentials for normal API calls, persistent
device sessions, explicit per-device revocation, and a bounded reauthentication
window. The original opaque session design required a PostgreSQL lookup on every
authenticated request and did not distinguish access from renewal credentials.

## Decision

- Passwords remain Argon2id hashes and login retains dummy verification for
  unknown email addresses.
- Registration accepts passwords between 8 and 128 characters. No composition
  rule is imposed; the interface encourages longer passphrases.
- Access tokens are HS256 JWTs valid for 15 minutes. They contain only `sub`,
  `iat`, `exp`, and `type=access`; verification is local. HS256 fits a single
  backend that both issues and verifies tokens. Its secret comes from settings.
- Refresh tokens are independent URL-safe random values with 256 bits of entropy.
  PostgreSQL stores only their SHA-256 hashes. A fast hash is appropriate because
  the token already has high entropy and the hash must support indexed lookup.
- A refresh token lasts up to 20 days. Successful use rotates it and extends its
  expiry to the earlier of 20 more days or the family's absolute expiry.
- Each login creates a distinct family with a fixed 90-day absolute expiry.
  Families model devices without adding speculative device metadata.
- Rotation locks the presented row and performs validation, revocation, and
  replacement in one database transaction. Concurrent uses cannot both rotate.
- Reuse of a token that already points to a replacement revokes the entire
  family. Other login families are unaffected.
- Logout receives the current refresh token and revokes only that row. Logout-all
  requires a valid access JWT and revokes every active refresh row for the user.
- Previously issued access JWTs remain valid until their 15-minute expiry; no
  access-token blacklist is maintained.

## Consequences

- Normal authenticated requests verify the JWT and load the user, but do not
  query the refresh-session table.
- Refresh, logout, and logout-all require PostgreSQL.
- A reuse alarm can invalidate the replacement returned to a racing legitimate
  request. This conservative behavior requires login again on that device.
- Mobile clients must keep refresh tokens in platform secure storage and replace
  them atomically after successful rotation.
- Changing a password must revoke all refresh sessions when that use case is
  introduced.
