import assert from 'node:assert/strict';
import test from 'node:test';

import { createPlanningRecord, listPlanningRecords } from '../src/planning/api.ts';
import { displayFinancialDate, financialDate, monthAtOffset, validFinancialDate, validatePlanningInput } from '../src/planning/validation.ts';
import { ApiError } from '../src/auth/api.ts';

test('planning validates positive exact monetary strings without rounding', () => {
  for (const amount of ['0', '0.00', '-1', '1.001', '1000000000000000000', 'NaN', '1e3', '1.000,00']) {
    assert.ok(validatePlanningInput('income', 'Synthetic', amount, 'ARS', '2026-10-01').error, amount);
  }
  for (const amount of ['0.01', '999999999999999999.99']) {
    assert.equal(validatePlanningInput('income', ' Synthetic ', amount, 'USD', '2026-10-01').input.amount, amount);
  }
  assert.equal(validatePlanningInput('commitments', 'Synthetic', '1,25', 'ARS', '2020-01-01').input.due_date, '2020-01-01');
  assert.equal(validatePlanningInput('income', 'Synthetic', '1,25', 'ARS', '2090-01-01').input.amount, '1.25');
  assert.ok(validatePlanningInput('income', ' ', '1', 'ARS', '2026-10-01').error);
  assert.ok(validatePlanningInput('income', 'x'.repeat(101), '1', 'ARS', '2026-10-01').error);
  assert.ok(validatePlanningInput('income', 'Synthetic', '1', 'EUR', '2026-10-01').error);
});

test('calendar validation and month rollover use Argentina financial dates', () => {
  assert.equal(financialDate(new Date('2026-10-01T02:59:59Z')), '2026-09-30');
  assert.equal(financialDate(new Date('2026-10-01T03:00:00Z')), '2026-10-01');
  assert.equal(displayFinancialDate('2026-10-15'), '15/10/2026');
  for (const date of ['2026-02-29', '2026-02-30', '0000-01-01', '2026-13-01', '2026-1-01', '2026-10-01T00:00:00Z']) assert.equal(validFinancialDate(date), false, date);
  for (const date of ['2024-02-29', '0001-01-01', '9999-12-31']) assert.equal(validFinancialDate(date), true, date);
});

test('monthly input retains its chosen day and uses exact decimal amounts', () => {
  const result = validatePlanningInput('income', 'Sueldo sintético', '15000,50', 'ARS', '31/01/2027', 'MONTHLY');
  assert.deepEqual(result.input, { description: 'Sueldo sintético', amount: '15000.50', currency: 'ARS', expected_date: '2027-01-31', recurrence: 'MONTHLY' });
  assert.equal(validatePlanningInput('commitments', 'Alquiler sintético', '10.25', 'USD', '05/10/2026', 'MONTHLY').input.due_date, '2026-10-05');
  assert.ok(validatePlanningInput('income', 'Synthetic', '1', 'ARS', '31/02/2027', 'MONTHLY').error);
  assert.ok(validatePlanningInput('income', 'Synthetic', '1', 'ARS', '05/10/2026', 'WEEKLY').error);
  assert.equal(monthAtOffset('2026-12-31', 1), '2027-01');
  assert.equal(monthAtOffset('2027-01-01', -1), '2026-12');
});

test('planning API uses owned paginated routes, exact strings and visible errors', async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.EXPO_PUBLIC_API_URL;
  process.env.EXPO_PUBLIC_API_URL = 'http://example.test';
  try {
    for (const kind of ['income', 'commitments']) {
      const input = validatePlanningInput(kind, 'Synthetic', '999999999999999999.99', 'USD', '2026-10-01').input;
      globalThis.fetch = async (url, options) => {
        assert.equal(url, `http://example.test/api/v1/${kind}`);
        assert.equal(options.headers.Authorization, 'Bearer synthetic');
        assert.deepEqual(JSON.parse(options.body), input);
        return new Response(JSON.stringify({ ...input, id: 'synthetic', status: 'PLANNED' }), { status: 201 });
      };
      assert.equal((await createPlanningRecord('synthetic', kind, input)).amount, input.amount);
      globalThis.fetch = async (url, options) => {
        assert.equal(url, `http://example.test/api/v1/${kind}?year=2026&month=10&include_overdue=true&limit=21&offset=20`);
        assert.equal(options.headers.Authorization, 'Bearer synthetic');
        return new Response('[]');
      };
      assert.deepEqual(await listPlanningRecords('synthetic', kind, '2026', '10', 20), []);
      for (const status of [401, 404, 422, 500]) {
        globalThis.fetch = async () => new Response('{}', { status });
        await assert.rejects(createPlanningRecord('synthetic', kind, input), (error) => error instanceof ApiError && error.statusCode === status && !!error.message);
      }
      globalThis.fetch = async () => { throw new Error('offline'); };
      await assert.rejects(listPlanningRecords('synthetic', kind, '2026', '10'), (error) => error instanceof ApiError && error.statusCode === null);
    }
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.EXPO_PUBLIC_API_URL;
    else process.env.EXPO_PUBLIC_API_URL = originalUrl;
  }
});
