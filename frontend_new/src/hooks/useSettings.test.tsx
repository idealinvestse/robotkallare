/// <reference types="vitest" />
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import api from '../api/axios';
import { useSettings, type AppSettings, SETTINGS_QUERY_KEY } from './useSettings';
import React from 'react';

// Mock data
const mockSettings: AppSettings = {
  ttsProvider: 'openai',
  ttsLanguage: 'sv-SE',
  ttsVoice: 'echo',
  ttsSpeed: 1.1,
  twilioFromNumber: '+1234567890',
  callTimeoutSec: 30,
  secondaryBackoffSec: 60,
  maxSecondaryAttempts: 3,
};

// Create a TanStack Query client for testing
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
      gcTime: 0,
      retry: false,
    },
    mutations: {
      retry: false,
    }
  },
});

// Mock the api client methods
let getSpy: vi.SpyInstance;
let putSpy: vi.SpyInstance;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(QueryClientProvider, { client: queryClient }, children);

describe('useSettings Hook', () => {
  beforeEach(() => {
    // Create spies before each test
    getSpy = vi.spyOn(api, 'get');
    putSpy = vi.spyOn(api, 'put');
  });

  afterEach(() => {
    // Restore original implementations after each test
    vi.restoreAllMocks();
    // Clear TanStack Query cache after each test
    queryClient.clear();
  });

  it('fetches settings successfully', async () => {
    // Mock the GET request
    getSpy.mockResolvedValue({ data: mockSettings });

    const { result, rerender } = renderHook(() => useSettings(), { wrapper });

    // Add act and a small delay to allow promises to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender(); // Rerender might be needed to pick up query state changes
    });

    await waitFor(() => expect(result.current.settingsQuery.isSuccess).toBe(true), { timeout: 5000 }); // Increase timeout

    expect(result.current.settingsQuery.data).toEqual(mockSettings);
    expect(result.current.settingsQuery.isLoading).toBe(false);
    expect(result.current.settingsQuery.isError).toBe(false);
  });

  it('handles fetch error', async () => {
    // Mock the GET request to return an error
    const error = new Error('Server Error');
    getSpy.mockRejectedValue(error);

    const { result, rerender } = renderHook(() => useSettings(), { wrapper });

    // Add act and a small delay to allow promises to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender();
    });

    await waitFor(() => expect(result.current.settingsQuery.isError).toBe(true), { timeout: 5000 }); // Increase timeout

    expect(result.current.settingsQuery.isError).toBe(true);
    expect(result.current.settingsQuery.error).toBeDefined();
    expect(result.current.settingsQuery.data).toBeUndefined();
  });

  it('saves settings successfully and updates query cache', async () => {
    const updatedSettings: AppSettings = {
      ...mockSettings,
      ttsSpeed: 1.5,
      callTimeoutSec: 45,
    };
    // Mock initial GET request
    getSpy.mockResolvedValue({ data: mockSettings });
    // Mock PUT request
    putSpy.mockResolvedValue({ data: updatedSettings });

    const { result, rerender } = renderHook(() => useSettings(), { wrapper });

    // Wait for initial fetch
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender(); // Rerender might be needed to pick up query state changes
    });

    await waitFor(() => expect(result.current.settingsQuery.isSuccess).toBe(true), { timeout: 5000 }); // Increase timeout
    expect(result.current.settingsQuery.data).toEqual(mockSettings);

    // Trigger mutation
    act(() => {
      result.current.saveSettings.mutate(updatedSettings);
    });

    // Add act and a small delay to allow promises to resolve for mutation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender();
    });

    // Wait for mutation to complete and cache to update
    await waitFor(() => expect(result.current.saveSettings.isSuccess).toBe(true), { timeout: 5000 });

    expect(result.current.saveSettings.isSuccess).toBe(true);
    // Verify cache is updated immediately by onSuccess
    await waitFor(() => expect(queryClient.getQueryData<AppSettings>(SETTINGS_QUERY_KEY)).toEqual(updatedSettings), { timeout: 5000 });
    // Check hook state as well
    expect(result.current.settingsQuery.data).toEqual(updatedSettings);
  });

  it('handles save error', async () => {
    const settingsToSave: AppSettings = { ...mockSettings, ttsSpeed: 1.5 };
    // Mock initial fetch
    getSpy.mockResolvedValueOnce({ data: mockSettings }); // Use Once if mocking sequence matters
    // Mock PUT request failure
    const saveError = new Error('Failed to save');
    putSpy.mockRejectedValue(saveError);

    const { result, rerender } = renderHook(() => useSettings(), { wrapper });

    // Wait for initial fetch
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender(); // Rerender might be needed to pick up query state changes
    });

    await waitFor(() => expect(result.current.settingsQuery.isSuccess).toBe(true), { timeout: 5000 }); // Increase timeout

    // Trigger mutation
    act(() => {
      result.current.saveSettings.mutate(settingsToSave);
    });

    // Add act and a small delay to allow promises to resolve for mutation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
      rerender();
    });

    // Wait for mutation to fail
    await waitFor(() => expect(result.current.saveSettings.isError).toBe(true), { timeout: 5000 });

    expect(result.current.saveSettings.isError).toBe(true);
    expect(result.current.saveSettings.error).toBeDefined();
    // Verify cache is NOT updated with failed data
    expect(queryClient.getQueryData<AppSettings>(SETTINGS_QUERY_KEY)).toEqual(mockSettings);
    // Verify hook state as well
    expect(result.current.settingsQuery.data).toEqual(mockSettings);
  });
});
