import React, { useState, useCallback } from 'react';
import { useContacts } from '../hooks/useContacts';
import { useGroups } from '../hooks/useGroups';
import { useCallStatus, triggerCall, manualCall, confirmCall, postponeCall } from '../hooks/useCallStatus';
import { ContactStatus } from '../types/operator';
import CallStatusPanel from '../components/CallStatusPanel';

// Status badge component with color coding for different statuses
const StatusBadge: React.FC<{ status: ContactStatus }> = ({ status }) => {
  const getStatusStyle = (status: ContactStatus) => {
    switch (status) {
      case 'CONFIRMED':
        return 'bg-green-100 text-green-700 border-green-400';
      case 'RINGING_PRIMARY':
      case 'RINGING_SECONDARY':
        return 'bg-blue-100 text-blue-700 border-blue-400 animate-pulse';
      case 'NO_ANSWER':
      case 'MANUAL_NEEDED':
        return 'bg-yellow-100 text-yellow-800 border-yellow-400';
      case 'ERROR':
        return 'bg-red-100 text-red-700 border-red-400';
      case 'PENDING':
      case 'SCHEDULED':
        return 'bg-gray-100 text-gray-700 border-gray-400';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-400';
    }
  };

  const getStatusLabel = (status: ContactStatus) => {
    switch (status) {
      case 'CONFIRMED': return 'Bekräftad';
      case 'RINGING_PRIMARY': return 'Ringer (Primär)';
      case 'RINGING_SECONDARY': return 'Ringer (Sekundär)';
      case 'NO_ANSWER': return 'Inget svar';
      case 'MANUAL_NEEDED': return 'Manuell åtgärd';
      case 'ERROR': return 'Fel';
      case 'PENDING': return 'Väntande';
      case 'SCHEDULED': return 'Schemalagd';
      default: return status;
    }
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getStatusStyle(status)}`}>
      {getStatusLabel(status)}
    </span>
  );
};

const OperatorDashboard: React.FC = () => {
  const { data: contacts, isLoading: contactsLoading, error: contactsError } = useContacts();
  const { data: groups, isLoading: groupsLoading, error: groupsError } = useGroups();
  const { data: callStatusData, isLoading: callStatusLoading, error: callStatusError } = useCallStatus();
  
  // Callback-funktioner för CallStatusPanel
  const handleTriggerCall = useCallback((contactId: string) => {
    triggerCall(contactId).then(() => {
      console.log(`Trigger call for: ${contactId}`);
    }).catch(error => {
      console.error('Error triggering call:', error);
    });
  }, []);
  
  const handleManualCall = useCallback((contactId: string) => {
    manualCall(contactId).then(() => {
      console.log(`Manual call for: ${contactId}`);
    }).catch(error => {
      console.error('Error initiating manual call:', error);
    });
  }, []);
  
  const handleConfirmCall = useCallback((contactId: string) => {
    confirmCall(contactId).then(() => {
      console.log(`Confirm call for: ${contactId}`);
    }).catch(error => {
      console.error('Error confirming call:', error);
    });
  }, []);
  
  const handlePostponeCall = useCallback((contactId: string, delayMinutes: number) => {
    postponeCall(contactId, delayMinutes).then(() => {
      console.log(`Postpone call for: ${contactId} by ${delayMinutes} minutes`);
    }).catch(error => {
      console.error('Error postponing call:', error);
    });
  }, []);

  // Laddnings-state
  if (contactsLoading || groupsLoading || callStatusLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-blue-500"></div>
          <p className="text-lg font-medium text-gray-700">Laddar data...</p>
        </div>
      </div>
    );
  }

  // Felhantering
  const error = contactsError || groupsError || callStatusError;
  if (error) {
    return (
      <div className="m-6 rounded-lg bg-red-50 p-4 text-red-800 shadow-sm">
        <h3 className="mb-2 font-bold">Ett fel uppstod</h3>
        <p>{error.message}</p>
        <button 
          className="mt-4 rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          onClick={() => window.location.reload()}
        >
          Försök igen
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header med titel */}
      <div className="bg-white p-6 border-b">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">GDial - Ringrobotens Kontrollpanel</h1>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Nytt utskick
          </button>
        </div>
      </div>
      
      <div className="p-6">
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Primär sektion - Samtalskontroll */}
          <div className="lg:col-span-2">
            <CallStatusPanel 
              contacts={contacts || []} 
              onTriggerCall={handleTriggerCall}
              onManualCall={handleManualCall}
              onConfirmCall={handleConfirmCall}
              onPostponeCall={handlePostponeCall}
            />
          </div>
          
          {/* Sidopanel med grupplista */}
          <div>
            <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
              <div className="p-4">
                <h3 className="text-lg font-medium">Kontaktgrupper</h3>
                <p className="text-sm text-gray-500 mt-1">Välj en grupp för att visa dess kontakter</p>
              </div>
              
              <div className="p-4 max-h-96 overflow-y-auto">
                <ul className="space-y-2">
                  {groups && groups.length > 0 ? (
                    groups.map(group => (
                      <li key={group.id} className="p-2 rounded hover:bg-gray-50 cursor-pointer">
                        <div className="font-medium">{group.name}</div>
                        <div className="text-sm text-gray-500">{group.contacts.length} kontakter</div>
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-500 text-sm">Inga grupper tillgängliga.</li>
                  )}
                </ul>
              </div>
              
              <div className="p-4 bg-gray-50">
                <button className="w-full px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Hantera grupper
                </button>
              </div>
            </div>
            
            {/* Snabblänkar */}
            <div className="mt-6 bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-medium mb-3">Snabbfunktioner</h3>
              <div className="grid grid-cols-2 gap-3">
                <button className="p-3 border rounded-md hover:bg-gray-50 flex flex-col items-center text-gray-700">
                  <svg className="w-6 h-6 mb-1 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <span className="text-sm">Mallar</span>
                </button>
                <button className="p-3 border rounded-md hover:bg-gray-50 flex flex-col items-center text-gray-700">
                  <svg className="w-6 h-6 mb-1 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm">Schemalägg</span>
                </button>
                <button className="p-3 border rounded-md hover:bg-gray-50 flex flex-col items-center text-gray-700">
                  <svg className="w-6 h-6 mb-1 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span className="text-sm">Rapporter</span>
                </button>
                <button className="p-3 border rounded-md hover:bg-gray-50 flex flex-col items-center text-gray-700">
                  <svg className="w-6 h-6 mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="text-sm">Inställningar</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OperatorDashboard;
