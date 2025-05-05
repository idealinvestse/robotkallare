import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';

export interface RealtimeCallEvent {
  eventType: 'initiated' | 'ringing' | 'in-progress' | 'completed' | 'failed' | 'busy' | 'no-answer';
  timestamp: string;
  callSid: string;
  contactId: string;
  contactName?: string;
  phoneNumber: string;
  direction: 'outbound' | 'inbound';
  duration?: number;
}

export interface ActiveCall {
  callSid: string;
  contactId: string;
  contactName?: string; 
  phoneNumber: string;
  status: RealtimeCallEvent['eventType'];
  startTime: string;
  direction: 'outbound' | 'inbound';
  duration?: number;
}

/**
 * Hook för att hämta och hantera realtidsstatus för aktiva samtal
 * Använder polling för att hålla UI uppdaterat
 * I en produktionsmiljö kan detta ersättas med WebSocket för realtidsuppdateringar
 */
export function useRealtimeCallStatus() {
  const queryClient = useQueryClient();
  
  // Hämta aktiva samtal
  const activeCalls = useQuery<ActiveCall[], Error>({
    queryKey: ['activeCalls'],
    queryFn: () => api.get<ActiveCall[]>('/api/v1/calls/active').then(res => res.data),
    refetchInterval: 3000, // Uppdatera var 3:e sekund
  });
  
  // Hämta de senaste samtalshändelserna (för realtidsuppdateringar)
  const recentEvents = useQuery<RealtimeCallEvent[], Error>({
    queryKey: ['callEvents', 'recent'],
    queryFn: () => api.get<RealtimeCallEvent[]>('/api/v1/calls/events?limit=10').then(res => res.data),
    refetchInterval: 2000, // Uppdatera var 2:a sekund
  });
  
  // Uppdatera samtalsstatus för en kontakt (används när operatören ändrar status manuellt)
  const updateCallStatus = useCallback(async (contactId: string, action: 'confirm' | 'retry' | 'cancel' | 'manual') => {
    try {
      await api.post(`/api/v1/calls/status/${contactId}`, { action });
      // Invalidera queries för att uppdatera data
      queryClient.invalidateQueries({ queryKey: ['activeCalls'] });
      queryClient.invalidateQueries({ queryKey: ['callEvents'] });
      return true;
    } catch (error) {
      console.error('Error updating call status:', error);
      return false;
    }
  }, [queryClient]);
  
  // Starta ett nytt utgående samtal
  const initiateCall = useCallback(async (contactId: string) => {
    try {
      const response = await api.post<{ callSid: string }>('/api/v1/calls/initiate', { contactId });
      // Invalidera queries för att uppdatera data
      queryClient.invalidateQueries({ queryKey: ['activeCalls'] });
      return response.data.callSid;
    } catch (error) {
      console.error('Error initiating call:', error);
      throw error;
    }
  }, [queryClient]);
  
  // Avsluta ett pågående samtal
  const terminateCall = useCallback(async (callSid: string) => {
    try {
      await api.post(`/api/v1/calls/${callSid}/terminate`);
      // Invalidera queries för att uppdatera data
      queryClient.invalidateQueries({ queryKey: ['activeCalls'] });
      return true;
    } catch (error) {
      console.error('Error terminating call:', error);
      return false;
    }
  }, [queryClient]);
  
  return {
    activeCalls,
    recentEvents,
    updateCallStatus,
    initiateCall,
    terminateCall
  };
}
