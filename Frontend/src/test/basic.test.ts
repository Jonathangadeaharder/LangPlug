import { describe, it, expect } from 'vitest';
import { assertArrayLength } from './assertion-helpers';

describe('Basic Test Suite', () => {
  it('WhenArithmeticPerformed_ThenReturnsCorrectResult', () => {
    expect(2 + 2).toBe(4);
  });

  it('WhenStringOperationsApplied_ThenReturnsTransformedString', () => {
    expect('hello'.toUpperCase()).toBe('HELLO');
  });

  it('WhenArrayCreated_ThenHasCorrectProperties', () => {
    const arr = [1, 2, 3];
    assertArrayLength(arr, 3);
    expect(arr.includes(2)).toBe(true);
  });

  it('WhenAsyncOperationExecuted_ThenResolvedValueReturned', async () => {
    const promise = Promise.resolve('test');
    const result = await promise;
    expect(result).toBe('test');
  });
});