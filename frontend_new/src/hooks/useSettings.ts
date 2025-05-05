import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';

export interface AppSettings {
  ttsProvider: 'openai' | 'twilio';
  ttsLanguage: string;
  ttsVoice: string;
  ttsSpeed: number; // 1.0 = normal
  twilioFromNumber: string;
  callTimeoutSec: number;
  secondaryBackoffSec: number;
  maxSecondaryAttempts: number;
}

export const SETTINGS_QUERY_KEY = ['appSettings'] as const;

export function useSettings() {
  const query = useQuery<AppSettings, Error>({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: async () => {
      const { data } = await api.get<AppSettings>('/api/v1/settings');
      return data;
    }
  });

  const qc = useQueryClient();

  const mutation = useMutation<AppSettings, Error, AppSettings>({
    mutationFn: async (newSettings: AppSettings) => {
      const { data } = await api.put<AppSettings>('/api/v1/settings', newSettings);
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(SETTINGS_QUERY_KEY, data);
    }
  });

  return { settingsQuery: query, saveSettings: mutation };
}
