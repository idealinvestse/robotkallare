import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { Contact, ContactStatus } from '../types/operator';

// Simulerade API-funktioner för att hantera samtalsstatus
// Dessa kommer att ersättas med faktiska anrop till backend API
export async function triggerCall(contactId: string): Promise<void> {
  // POST /api/v1/outreach/trigger-call
  return api.post('/api/v1/outreach/trigger-call', { contactId });
}

export async function manualCall(contactId: string): Promise<void> {
  // POST /api/v1/outreach/manual-call
  return api.post('/api/v1/outreach/manual-call', { contactId });
}

export async function confirmCall(contactId: string): Promise<void> {
  // POST /api/v1/outreach/confirm-call
  return api.post('/api/v1/outreach/confirm-call', { contactId });
}

export async function postponeCall(contactId: string, delayMinutes: number): Promise<void> {
  // POST /api/v1/outreach/postpone-call
  return api.post('/api/v1/outreach/postpone-call', { contactId, delayMinutes });
}

/**
 * Hook för att hämta aktiva samtalsstatus - kommer refetchas regelbundet
 * för att hålla UI uppdaterat med senaste data från ringroboten
 */
export function useCallStatus() {
  return useQuery<Contact[], Error>({
    queryKey: ['callStatus'],
    queryFn: () => api.get<Contact[]>('/api/v1/outreach/status').then(res => res.data),
    refetchInterval: 5000, // Uppdatera data var 5e sekund för realtids-känsla
  });
}
