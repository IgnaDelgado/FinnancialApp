import assert from 'node:assert/strict';
import test from 'node:test';

import { validateRegistration } from '../src/auth/registrationValidation.ts';

test('registration explains missing or malformed email', () => {
  assert.match(validateRegistration('sin-arroba', 'password1', 'password1').email, /correo válido/);
  assert.match(validateRegistration('persona@', 'password1', 'password1').email, /correo válido/);
  assert.equal(validateRegistration('persona+test@example.com', 'password1', 'password1').email, undefined);
});

test('registration explains password boundaries', () => {
  assert.match(validateRegistration('a@example.com', '1234567', '1234567').password, /al menos 8/);
  assert.equal(validateRegistration('a@example.com', '12345678', '12345678').password, undefined);
  assert.equal(validateRegistration('a@example.com', 'a'.repeat(128), 'a'.repeat(128)).password, undefined);
  assert.match(validateRegistration('a@example.com', 'a'.repeat(129), 'a'.repeat(129)).password, /128/);
});

test('registration counts Unicode code points like the backend', () => {
  assert.match(validateRegistration('a@example.com', '😀'.repeat(7), '😀'.repeat(7)).password, /al menos 8/);
});

test('registration explains missing and mismatched confirmation', () => {
  assert.match(validateRegistration('a@example.com', 'password1', '').confirmation, /Repetí/);
  assert.match(validateRegistration('a@example.com', 'password1', 'password2').confirmation, /no coinciden/);
  assert.deepEqual(validateRegistration('a@example.com', 'password1', 'password1'), {});
});
