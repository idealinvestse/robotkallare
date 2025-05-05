import React from 'react';
import { useRealtimeCallStatus, RealtimeCallEvent } from '../hooks/useRealtimeCallStatus';

interface RealtimeCallMonitorProps {
  className?: string;
}

/**
 * Komponent för realtidsövervakning av pågående samtal
 * Visar livefeed av samtalshändelser och pågående samtal
 */
const RealtimeCallMonitor: React.FC<RealtimeCallMonitorProps> = ({ className = '' }) => {
  const { 
    activeCalls: { data: calls = [], isLoading: callsLoading, error: callsError },
    recentEvents: { data: events = [], isLoading: eventsLoading, error: eventsError },
    terminateCall,
    updateCallStatus
  } = useRealtimeCallStatus();
  
  const isLoading = callsLoading || eventsLoading;
  const error = callsError || eventsError;

  // Formatera tid för händelser
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('sv-SE', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  // Formatera samtalslängd
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '00:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };
  
  // Beräkna samtalstid baserat på start tid (för pågående samtal)
  const calculateDuration = (startTime: string) => {
    const start = new Date(startTime).getTime();
    const now = new Date().getTime();
    const durationMs = now - start;
    return Math.floor(durationMs / 1000); // konvertera till sekunder
  };
  
  // Generera händelsestatus-text och färg
  const getEventStatusInfo = (eventType: RealtimeCallEvent['eventType']) => {
    const statusMap: Record<RealtimeCallEvent['eventType'], { text: string, color: string }> = {
      'initiated': { text: 'Startat', color: 'text-blue-600' },
      'ringing': { text: 'Ringer', color: 'text-blue-600' },
      'in-progress': { text: 'Pågående', color: 'text-green-600' },
      'completed': { text: 'Avslutad', color: 'text-green-600' },
      'failed': { text: 'Misslyckades', color: 'text-red-600' },
      'busy': { text: 'Upptagen', color: 'text-yellow-600' },
      'no-answer': { text: 'Inget svar', color: 'text-yellow-600' }
    };
    
    return statusMap[eventType] || { text: eventType, color: 'text-gray-600' };
  };
  
  // Hantera när operatören avbryter ett samtal
  const handleTerminateCall = async (callSid: string) => {
    try {
      await terminateCall(callSid);
    } catch (error) {
      console.error('Failed to terminate call:', error);
      // Visa felmeddelande till användaren här
    }
  };
  
  // Hantera uppdatering av samtalsstatus (t.ex. markera som bekräftad)
  const handleUpdateStatus = async (contactId: string, action: 'confirm' | 'retry' | 'cancel' | 'manual') => {
    try {
      await updateCallStatus(contactId, action);
    } catch (error) {
      console.error('Failed to update call status:', error);
      // Visa felmeddelande till användaren här
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="ml-2 text-gray-600">Laddar samtalsinformation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="bg-red-50 p-4 rounded-md text-red-800">
          <p className="font-medium">Ett fel uppstod vid hämtning av samtalsdata</p>
          <p className="mt-1 text-sm">{error.message}</p>
          <button className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded-md text-sm hover:bg-red-200">
            Försök igen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Realtidsövervakning</h3>
        <div className="flex items-center">
          <span className="relative flex h-3 w-3 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span className="text-sm text-green-600 font-medium">Live</span>
        </div>
      </div>

      {/* Aktiva samtal */}
      <div className="p-4 border-b">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Pågående samtal ({calls.length})</h4>
        
        {calls.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            <p>Inga aktiva samtal just nu</p>
          </div>
        ) : (
          <div className="space-y-3">
            {calls.map(call => (
              <div key={call.callSid} className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{call.contactName || 'Okänd kontakt'}</p>
                    <p className="text-sm text-gray-600">{call.phoneNumber}</p>
                  </div>
                  <div className="flex items-center">
                    <div className="text-sm font-medium mr-3">
                      {/* Timer för samtalslängd */}
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDuration(call.duration || calculateDuration(call.startTime))}
                      </span>
                    </div>
                    <button 
                      onClick={() => handleTerminateCall(call.callSid)}
                      className="p-1 rounded-full hover:bg-red-100 text-red-600"
                      title="Avbryt samtal"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
                
                <div className="mt-2 flex">
                  {/* Status och åtgärdsknappar */}
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-800 text-xs">
                    <span className="relative flex h-2 w-2 mr-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
                    </span>
                    {getEventStatusInfo(call.status).text}
                  </span>
                  
                  <div className="ml-auto flex space-x-2">
                    <button 
                      onClick={() => handleUpdateStatus(call.contactId, 'confirm')}
                      className="px-2 py-1 text-xs rounded bg-green-100 text-green-800 hover:bg-green-200"
                    >
                      Bekräfta
                    </button>
                    <button 
                      onClick={() => handleUpdateStatus(call.contactId, 'manual')}
                      className="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                    >
                      Markera för manuell
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Senaste händelser */}
      <div className="p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Senaste händelser</h4>
        
        <div className="max-h-60 overflow-y-auto">
          {events.length === 0 ? (
            <div className="text-center py-4 text-gray-500">
              <p>Inga samtalsaktiviteter än</p>
            </div>
          ) : (
            <div className="space-y-2">
              {events.map((event, index) => {
                const { text, color } = getEventStatusInfo(event.eventType);
                
                return (
                  <div key={`${event.callSid}-${index}`} className="text-sm border-l-2 border-gray-200 pl-3 py-1">
                    <div className="flex justify-between text-gray-500">
                      <span>{formatTime(event.timestamp)}</span>
                      <span className={color}>{text}</span>
                    </div>
                    <div className="font-medium">{event.contactName || 'Okänd kontakt'}</div>
                    <div className="text-gray-600">{event.phoneNumber}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealtimeCallMonitor;
