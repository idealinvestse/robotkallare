/// <reference types="vitest" />
import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, afterEach, vi } from 'vitest';
import api from '../api/axios';
import { useSmsHistory } from './useSmsHistory';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Set shorter stale time & gc time + disable retries for tests
      staleTime: 0,
      gcTime: 0, // Use gcTime instead of cacheTime
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(QueryClientProvider, { client: queryClient }, children);

describe('useSmsHistory', () => {
  let getSpy: vi.SpyInstance;

  afterEach(() => {
    // Clean up mock adapter after each test
    vi.restoreAllMocks();
    // Clear TanStack Query cache after each test
    queryClient.clear();
  });

  it('fetches sms history successfully', async () => {
    getSpy = vi.spyOn(api, 'get');
    getSpy.mockResolvedValue({
      data: {
        messages: [
          {
            id: '1',
            contactId: 'c1',
            contactName: 'Test Kontakt',
            phoneNumber: '+46700000001',
            message: 'Hej!',
            status: 'sent',
            sentTime: '2025-05-05T01:00:00Z',
            messageType: 'custom'
          }
        ],
        total: 1
      }
    });
    const { result } = renderHook(() => useSmsHistory(1, 10), { wrapper });

    // Add act and a small delay to allow promises to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Wait for the hook to finish fetching with increased timeout
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });

    expect(result.current.isSuccess).toBe(true);
    expect(result.current.data?.messages).toHaveLength(1);
    expect(result.current.data?.messages[0].message).toBe('Hej!');
  });

  it('handles error', async () => {
    getSpy = vi.spyOn(api, 'get');
    const error = new Error('Network Error');
    getSpy.mockRejectedValue(error);
    const { result } = renderHook(() => useSmsHistory(1, 10), { wrapper });

    // Add act and a small delay to allow promises to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Wait for the hook to encounter an error with increased timeout
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeDefined();
  });
});
