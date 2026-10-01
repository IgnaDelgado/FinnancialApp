import assert from 'node:assert/strict';
import test from 'node:test';

import { completeGlobalSignOut } from '../src/auth/globalSignOut.ts';

test('failed global revocation keeps the local session available to retry', async () => {
  const effects = [];
  await assert.rejects(
    completeGlobalSignOut(
      async () => { effects.push('revoke'); throw new Error('offline'); },
      async () => { effects.push('clear-token'); },
      () => { effects.push('clear-session'); },
    ),
    /offline/,
  );
  assert.deepEqual(effects, ['revoke']);
});

test('successful global revocation clears local credentials and session', async () => {
  const effects = [];
  await completeGlobalSignOut(
    async () => { effects.push('revoke'); },
    async () => { effects.push('clear-token'); },
    () => { effects.push('clear-session'); },
  );
  assert.deepEqual(effects, ['revoke', 'clear-token', 'clear-session']);
});

test('local storage failure after revocation still clears the visible session', async () => {
  const effects = [];
  await assert.rejects(
    completeGlobalSignOut(
      async () => { effects.push('revoke'); },
      async () => { effects.push('clear-token'); throw new Error('storage'); },
      () => { effects.push('clear-session'); },
    ),
    /storage/,
  );
  assert.deepEqual(effects, ['revoke', 'clear-token', 'clear-session']);
});
