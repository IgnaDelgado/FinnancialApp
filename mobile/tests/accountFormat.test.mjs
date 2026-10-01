import assert from 'node:assert/strict';
import test from 'node:test';

import { formatMoney, normalizeMoneyInput } from '../src/accounts/format.ts';

test('account balance accepts zero, comma decimals, and the supported precision', () => {
  assert.equal(normalizeMoneyInput('0'), '0');
  assert.equal(normalizeMoneyInput(' 30000,75 '), '30000.75');
  assert.equal(normalizeMoneyInput('999999999999999999.99'), '999999999999999999.99');
});

test('account balance rejects ambiguous, imprecise, and out-of-range input', () => {
  for (const value of ['', '-1', '1.000,00', '1,001', '01', '1000000000000000000.00']) {
    assert.equal(normalizeMoneyInput(value), null, value);
  }
});

test('account balances keep currency and negative sign visible', () => {
  assert.equal(formatMoney('30000.75', 'ARS'), 'ARS 30.000,75');
  assert.equal(formatMoney('-30000.00', 'USD'), 'USD -30.000,00');
  assert.equal(formatMoney('0.00', 'ARS'), 'ARS 0,00');
});
