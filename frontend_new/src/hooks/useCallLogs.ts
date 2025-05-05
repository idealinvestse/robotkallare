import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';

export interface CallLog {
  id: string;
  contactId: string;
  contactName: string;
  phoneNumber: string;
  startTime: string;
  endTime?: string;
  duration?: number; // in seconds
  status: 'completed' | 'no-answer' | 'busy' | 'failed' | 'canceled';
  recordingUrl?: string;
  callSid: string; // Twilio Call SID
  notes?: string;
}

/**
 * Hämtar samtalsloggar från backend
 * @param limit Max antal loggar att hämta
 * @param page Sidnummer för paginering
 * @param contactId Filtrera på specifik kontakt (valfritt)
 */
export function useCallLogs(limit: number = 50, page: number = 1, contactId?: string) {
  return useQuery<{ logs: CallLog[], total: number }, Error>({
    queryKey: ['callLogs', limit, page, contactId],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: limit.toString(),
        page: page.toString()
      });
      
      if (contactId) {
        params.append('contactId', contactId);
      }
      
      const response = await api.get<{ logs: CallLog[], total: number }>(`/api/v1/call-logs?${params.toString()}`);
      return response.data;
    },
    // Hämta nya loggar var 30:e sekund
    refetchInterval: 30000,
  });
}
