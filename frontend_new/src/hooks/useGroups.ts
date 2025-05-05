import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { Group } from '../types/operator';

/**
 * Hook for fetching all groups from backend.
 */
export function useGroups() {
  return useQuery<Group[], Error>({
    queryKey: ['groups'],
    queryFn: () => api.get<Group[]>('/api/groups').then(res => res.data),
  });
}
