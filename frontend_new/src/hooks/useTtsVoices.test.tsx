/// <reference types="vitest" />
import React from 'react';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest';
import api from '../api/axios';
import { useTtsVoices, type TtsVoice } from './useTtsVoices';
import { AppSettings } from './useSettings';

// Mock data
const mockVoices: TtsVoice[] = [
  { id: 'sv-SE-Wavenet-A', name: 'Svenska - Kvinna (Wavenet A)', language: 'sv-SE', gender: 'female' },
  { id: 'sv-SE-Wavenet-B', name: 'Svenska - Man (Wavenet B)', language: 'sv-SE', gender: 'male' },
];

// Setup
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
      gcTime: 0,
      retry: false,
    },
  },
});

let getSpy: vi.SpyInstance;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(QueryClientProvider, { client: queryClient }, children);

describe('useTtsVoices Hook', () => {
  beforeEach(() => {
    // Create spy before each test
    getSpy = vi.spyOn(api, 'get');
    queryClient.clear(); // Clear cache before each test
  });

  afterEach(() => {
    // Restore original implementation after each test
    vi.restoreAllMocks();
  });

  it('fetches voices successfully when provider and language are provided', async () => {
    const provider = 'openai';
    const language = 'sv-SE';
    // Mock the GET request
    getSpy.mockResolvedValue({ data: mockVoices });

    const { result } = renderHook(() => useTtsVoices(provider, language), { wrapper });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });

    expect(result.current.data).toEqual(mockVoices);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('does not fetch if provider is missing', () => {
    const provider = '';
    const language = 'sv-SE';
    // Hook call with empty provider (note: this might still show TS error locally if types enforce 'openai'|'twilio')
    // The test relies on the 'enabled' flag logic within the hook.
    // Use type assertion to bypass strict type check for this specific test case
    const { result } = renderHook(() => useTtsVoices(provider as AppSettings['ttsProvider'], language), { wrapper });

    // Hook should not be enabled and thus not fetching
    expect(result.current.isFetching).toBe(false);
    expect(result.current.status).toBe('pending'); // Or 'idle' depending on RQ version
    // Check that API was not called
    expect(getSpy).not.toHaveBeenCalled();
  });

  it('does not fetch if language is missing', () => {
    const provider = 'openai';
    const language = '';
    const { result } = renderHook(() => useTtsVoices(provider, language), { wrapper });

    expect(result.current.status).toBe('pending');
    expect(result.current.data).toBeUndefined();
    expect(getSpy).not.toHaveBeenCalled();
  });

  it('handles fetch error', async () => {
    const provider = 'openai';
    const language = 'sv-SE';
    // Mock the GET request to return an error
    const error = new Error('Fetch failed');
    getSpy.mockRejectedValue(error);

    const { result, rerender } = renderHook(() => useTtsVoices(provider, language), { wrapper });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender();
    });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeDefined();
    expect(result.current.data).toBeUndefined();
  });
});
