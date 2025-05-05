import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { AppSettings } from './useSettings'; // Importera AppSettings

export interface TtsVoice {
  id: string; // Use ID from provider
  name: string; // Display name
  language: string;
  gender?: 'male' | 'female';
}

export function useTtsVoices(provider: AppSettings['ttsProvider'], language: string) {
  return useQuery<TtsVoice[], Error>({
    queryKey: ['ttsVoices', provider, language],
    queryFn: async () => {
      const { data } = await api.get<TtsVoice[]>(`/api/v1/tts/voices?provider=${provider}&language=${language}`);
      return data;
    },
    enabled: !!provider && !!language
  });
}
