import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { Contact } from '../types/operator';

/**
 * Hook for fetching all contacts from backend.
 */
export function useContacts() {
  return useQuery<Contact[], Error>({
    queryKey: ['contacts'],
    queryFn: () => api.get<Contact[]>('/api/contacts').then(res => res.data),
  });
}
