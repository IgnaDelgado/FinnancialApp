import assert from 'node:assert/strict';
import test from 'node:test';
import { previewExpense } from '../src/home/preview.ts';

test('expense preview subtracts exact cents and keeps shortfalls visible', () => {
  assert.equal(previewExpense('100.10', '20,05'), '80.05');
  assert.equal(previewExpense('0.00', '0.01'), '-0.01');
  assert.equal(previewExpense('-0.01', '0.01'), '-0.02');
  assert.equal(previewExpense('999999999999999999.99', '0.01'), '999999999999999999.98');
  assert.equal(previewExpense('100.00', '100'), '0.00');
});

test('expense preview rejects zero, negative, imprecise and ambiguous input', () => {
  for (const input of ['', '0', '0.00', '-1', '1.001', '1.000,00', 'Infinity', '1000000000000000000']) {
    assert.equal(previewExpense('100.00', input), null, input);
  }
});
