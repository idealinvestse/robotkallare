import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';

export interface SmsMessage {
  id: string;
  contactId: string;
  contactName: string;
  phoneNumber: string;
  message: string;
  status: 'sent' | 'delivered' | 'failed' | 'queued';
  sentTime: string;
  deliveredTime?: string;
  messageType: 'template' | 'custom';
  templateId?: string;
  templateName?: string;
  campaign?: {
    id: string;
    name: string;
  };
}

export interface SmsHistoryResponse {
  messages: SmsMessage[];
  total: number;
}

/**
 * Hämtar historik över SMS-utskick från backend
 * Stöd för filtrering, paginering och sökning
 */
export function useSmsHistory(
  page: number = 1, 
  limit: number = 25, 
  filters: {
    contactId?: string;
    campaignId?: string;
    status?: SmsMessage['status'];
    startDate?: string;
    endDate?: string;
    search?: string;
  } = {}
) {
  return useQuery<SmsHistoryResponse, Error>({
    queryKey: ['smsHistory', page, limit, filters],
    queryFn: async () => {
      // Bygg query-parametrar
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString()
      });
      
      // Lägg till filter-parametrar
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });
      
      const response = await api.get<SmsHistoryResponse>(`/api/v1/sms/history?${params.toString()}`);
      return response.data;
    }
  });
}

/**
 * Hämta statistik för SMS-utskick
 * Returnerar antal per status och övergripande framgångsgrad
 */
export function useSmsStats(
  period: 'day' | 'week' | 'month' | 'all' = 'day',
  campaignId?: string
) {
  return useQuery<{
    total: number;
    sent: number;
    delivered: number;
    failed: number;
    queued: number;
    successRate: number;
  }, Error>({
    queryKey: ['smsStats', period, campaignId],
    queryFn: async () => {
      // Bygg query-parametrar
      const params = new URLSearchParams({
        period
      });
      
      if (campaignId) {
        params.append('campaignId', campaignId);
      }
      
      const response = await api.get<any>(`/api/v1/sms/stats?${params.toString()}`);
      return response.data;
    }
  });
}

/**
 * Hook för att skicka custom SMS via API
 * Används för manuella utskick från operatören
 */
export function useSendSms() {
  const queryClient = useQueryClient();
  
  const sendSms = async (
    payload: {
      contactId: string;
      message: string;
    } | {
      contactIds: string[];
      message: string;
    } | {
      groupId: string;
      message: string;
    } | {
      phoneNumber: string;
      message: string;
    }
  ) => {
    try {
      const response = await api.post('/api/v1/sms/send', payload);
      // Invalidera queries för att uppdatera historik
      queryClient.invalidateQueries({ queryKey: ['smsHistory'] });
      queryClient.invalidateQueries({ queryKey: ['smsStats'] });
      return response.data;
    } catch (error) {
      console.error('Error sending SMS:', error);
      throw error;
    }
  };
  
  return { sendSms };
}

/**
 * Hook för att skicka ett SMS baserat på en fördefinierad mall
 */
export function useSendTemplateSms() {
  const queryClient = useQueryClient();
  
  const sendTemplateSms = async (
    payload: {
      templateId: string;
      contactId: string;
      parameters?: Record<string, string>;
    } | {
      templateId: string;
      contactIds: string[];
      parameters?: Record<string, string>;
    } | {
      templateId: string;
      groupId: string;
      parameters?: Record<string, string>;
    }
  ) => {
    try {
      const response = await api.post('/api/v1/sms/send-template', payload);
      // Invalidera queries för att uppdatera historik
      queryClient.invalidateQueries({ queryKey: ['smsHistory'] });
      queryClient.invalidateQueries({ queryKey: ['smsStats'] });
      return response.data;
    } catch (error) {
      console.error('Error sending template SMS:', error);
      throw error;
    }
  };
  
  return { sendTemplateSms };
}
