# ADR 0001: MVP authentication mechanism

## Status

Superseded by [ADR 0002](0002-jwt-refresh-sessions.md).

## Context

The application needs registration, login, logout, secure password storage, and
strict isolation of user-owned resources. The first client will eventually be a
mobile application. The MVP does not require social login, multi-factor
authentication, or account recovery.

## Decision

- A normalized email address is the authentication identifier.
- Email addresses are stored in lowercase and are unique.
- Passwords are hashed with Argon2id. Plain-text passwords are never persisted
  or logged.
- Successful login creates an opaque, cryptographically random session token.
- Only a SHA-256 hash of the session token is persisted. The raw token is shown
  only in the login response and will later be stored by the mobile client in
  platform-provided secure storage.
- Every authenticated request validates the session against PostgreSQL.
- Logout revokes the server-side session immediately.
- Sessions expire after 30 days. The lifetime will be configuration rather than
  a value supplied by clients.
- User identifiers are application-generated UUID v4 values.
- ARS and USD are the supported reference currencies; ARS is the default.
- Account recovery, social login, and multi-factor authentication are deferred.

## Alternatives considered

### Stateless JWT access and refresh tokens

Rejected for the MVP because immediate logout and token revocation require
additional state or short token lifetimes plus refresh-token rotation. Opaque
sessions provide the required behavior with fewer moving parts.

### Redis-backed sessions

Rejected because PostgreSQL is already required and the expected MVP load does
not justify another operational dependency.

### Provider-based OAuth

Rejected because social login is outside MVP scope and would add external
provider, callback, and secret-management requirements.

## Consequences

- Authentication requires one indexed database lookup per request.
- Logout and administrative revocation are straightforward.
- A database outage makes authenticated operations unavailable, which is
  consistent with the rest of the application.
- Session cleanup and secure mobile storage must be implemented before public
  release.
