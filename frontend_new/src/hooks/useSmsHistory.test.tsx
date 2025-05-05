import React from 'react';
import { renderHook } from '@testing-library/react-hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { useSmsHistory } from './useSmsHistory';

const mock = new MockAdapter(axios);
const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(QueryClientProvider, { client: queryClient }, children);

describe('useSmsHistory', () => {
  afterEach(() => {
    mock.reset();
    queryClient.clear();
  });

  it('fetches sms history successfully', async () => {
    mock.onGet(/\/api\/v1\/sms\/history.*/).reply(200, {
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
    });
    const { result, waitFor } = renderHook(() => useSmsHistory(1, 10), { wrapper });
    await waitFor(() => result.current.isSuccess);
    expect(result.current.data?.messages).toHaveLength(1);
    expect(result.current.data?.messages[0].message).toBe('Hej!');
  });

  it('handles error', async () => {
    mock.onGet(/\/api\/v1\/sms\/history.*/).reply(500);
    const { result, waitFor } = renderHook(() => useSmsHistory(1, 10), { wrapper });
    await waitFor(() => result.current.isError);
    expect(result.current.error).toBeDefined();
  });
});
