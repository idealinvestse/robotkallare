import React from 'react';
import { Contact, ContactStatus } from '../types/operator';

interface CallStatusPanelProps {
  contacts: Contact[];
  onTriggerCall: (contactId: string) => void;
  onManualCall: (contactId: string) => void;
  onConfirmCall: (contactId: string) => void;
  onPostponeCall: (contactId: string, delayMinutes: number) => void;
}

// Gruppera kontakter efter status för tydlig överblick
const groupContactsByStatus = (contacts: Contact[]) => {
  const statusGroups: Record<string, Contact[]> = {
    active: [], // Ringande samtal
    pending: [], // Väntande samtal
    completed: [], // Bekräftade samtal
    problematic: [], // Problem/manuell åtgärd
  };

  contacts.forEach(contact => {
    switch (contact.status) {
      case 'RINGING_PRIMARY':
      case 'RINGING_SECONDARY':
        statusGroups.active.push(contact);
        break;
      case 'PENDING':
      case 'SCHEDULED':
        statusGroups.pending.push(contact);
        break;
      case 'CONFIRMED':
        statusGroups.completed.push(contact);
        break;
      case 'NO_ANSWER':
      case 'MANUAL_NEEDED':
      case 'ERROR':
        statusGroups.problematic.push(contact);
        break;
      default:
        statusGroups.pending.push(contact);
    }
  });

  return statusGroups;
};

// Status icon component med animering och färger
const StatusIcon: React.FC<{ status: ContactStatus; size?: 'sm' | 'md' | 'lg' }> = ({ status, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const getIconByStatus = (status: ContactStatus) => {
    switch (status) {
      case 'RINGING_PRIMARY':
      case 'RINGING_SECONDARY':
        return (
          <div className={`relative ${sizeClasses[size]}`}>
            <div className="absolute inset-0 rounded-full bg-blue-500 animate-ping opacity-75"></div>
            <div className="relative rounded-full bg-blue-500"></div>
          </div>
        );
      case 'CONFIRMED':
        return (
          <svg className={`${sizeClasses[size]} text-green-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'NO_ANSWER':
        return (
          <svg className={`${sizeClasses[size]} text-yellow-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'MANUAL_NEEDED':
        return (
          <svg className={`${sizeClasses[size]} text-yellow-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case 'ERROR':
        return (
          <svg className={`${sizeClasses[size]} text-red-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'PENDING':
      case 'SCHEDULED':
      default:
        return (
          <svg className={`${sizeClasses[size]} text-gray-400`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return getIconByStatus(status);
};

// Formatera timestampen för senaste och nästa försök
const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString('sv-SE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Huvudkomponenten
const CallStatusPanel: React.FC<CallStatusPanelProps> = ({
  contacts,
  onTriggerCall,
  onManualCall,
  onConfirmCall,
  onPostponeCall
}) => {
  const statusGroups = groupContactsByStatus(contacts);

  // Räkna antal för varje statusgrupp
  const activeCount = statusGroups.active.length;
  const pendingCount = statusGroups.pending.length;
  const problematicCount = statusGroups.problematic.length;
  const completedCount = statusGroups.completed.length;
  const totalCount = contacts.length;
  const completionPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Call Status Header */}
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold flex items-center">
          <svg className="w-6 h-6 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
          </svg>
          Ringrobotens Status
        </h2>
      </div>

      {/* Status Dashboard */}
      <div className="p-4 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="p-3 bg-white rounded border-l-4 border-blue-500 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Aktiva samtal</div>
            <div className="mt-1 flex items-baseline">
              <div className="text-2xl font-semibold text-blue-600">{activeCount}</div>
              <div className="ml-2 text-sm text-gray-600">av {totalCount}</div>
            </div>
          </div>

          <div className="p-3 bg-white rounded border-l-4 border-gray-400 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Väntande samtal</div>
            <div className="mt-1 flex items-baseline">
              <div className="text-2xl font-semibold text-gray-600">{pendingCount}</div>
              <div className="ml-2 text-sm text-gray-600">av {totalCount}</div>
            </div>
          </div>

          <div className="p-3 bg-white rounded border-l-4 border-yellow-500 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Åtgärd krävs</div>
            <div className="mt-1 flex items-baseline">
              <div className="text-2xl font-semibold text-yellow-600">{problematicCount}</div>
              <div className="ml-2 text-sm text-gray-600">av {totalCount}</div>
            </div>
          </div>

          <div className="p-3 bg-white rounded border-l-4 border-green-500 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Bekräftade</div>
            <div className="mt-1 flex items-baseline">
              <div className="text-2xl font-semibold text-green-600">{completedCount}</div>
              <div className="ml-2 text-sm text-gray-600">av {totalCount}</div>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Samtalsstatus</span>
            <span className="text-sm font-medium text-gray-700">{completionPercentage}% bekräftade</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-green-600 h-2.5 rounded-full" style={{ width: `${completionPercentage}%` }}></div>
          </div>
        </div>
      </div>

      {/* Active Calls */}
      {activeCount > 0 && (
        <div className="p-4 border-t">
          <h3 className="font-medium text-gray-900 flex items-center mb-3">
            <div className="mr-2 relative">
              <div className="absolute inset-0 rounded-full bg-blue-500 animate-ping opacity-75"></div>
              <div className="relative rounded-full bg-blue-500 h-2 w-2"></div>
            </div>
            Aktiva samtal
          </h3>
          <ul className="divide-y divide-gray-200">
            {statusGroups.active.map(contact => (
              <li key={contact.id} className="py-3 flex justify-between items-center">
                <div className="flex items-center">
                  <StatusIcon status={contact.status} />
                  <span className="ml-2 font-medium">{contact.name}</span>
                  <span className="ml-2 text-sm text-gray-500">{contact.primaryPhone}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-xs text-gray-500 bg-gray-100 rounded px-2 py-1">
                    {contact.status === 'RINGING_PRIMARY' ? 'Primärt nummer' : 'Sekundärt nummer'}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Problem Calls - Needs Operator Action */}
      {problematicCount > 0 && (
        <div className="p-4 border-t bg-yellow-50">
          <h3 className="font-medium text-gray-900 flex items-center mb-3">
            <svg className="w-5 h-5 mr-1 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Åtgärd krävs
          </h3>
          <ul className="divide-y divide-yellow-100">
            {statusGroups.problematic.map(contact => (
              <li key={contact.id} className="py-3">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center">
                    <StatusIcon status={contact.status} />
                    <span className="ml-2 font-medium">{contact.name}</span>
                    <span className="ml-2 text-sm text-gray-500">{contact.primaryPhone}</span>
                  </div>
                  <div>
                    <span className="text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-800 border border-yellow-300">
                      {contact.status === 'NO_ANSWER' ? 'Inget svar' : 
                       contact.status === 'MANUAL_NEEDED' ? 'Manuell åtgärd' : 'Fel'}
                    </span>
                  </div>
                </div>
                
                <div className="text-xs text-gray-500 mb-2">
                  {contact.lastAttemptTime && (
                    <span>Senaste försök: {formatTimestamp(contact.lastAttemptTime)}</span>
                  )}
                </div>
                
                <div className="flex space-x-2 mt-2">
                  <button 
                    onClick={() => onManualCall(contact.id)}
                    className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700"
                  >
                    Ring manuellt
                  </button>
                  <button 
                    onClick={() => onConfirmCall(contact.id)}
                    className="px-3 py-1 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700"
                  >
                    Markera bekräftad
                  </button>
                  <button 
                    onClick={() => onPostponeCall(contact.id, 15)}
                    className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded hover:bg-gray-200"
                  >
                    Skjut upp (15 min)
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pending Calls */}
      {pendingCount > 0 && (
        <div className="p-4 border-t">
          <h3 className="font-medium text-gray-900 flex items-center mb-3">
            <svg className="w-5 h-5 mr-1 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            Väntande samtal
          </h3>
          <ul className="divide-y divide-gray-200 max-h-60 overflow-y-auto">
            {statusGroups.pending.map(contact => (
              <li key={contact.id} className="py-2 flex justify-between items-center">
                <div className="flex items-center">
                  <StatusIcon status={contact.status} size="sm" />
                  <span className="ml-2 text-sm">{contact.name}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-xs text-gray-500">
                    {contact.nextAttemptTime ? 
                      `Nästa: ${formatTimestamp(contact.nextAttemptTime)}` : 'Väntar...'}
                  </span>
                  <button 
                    onClick={() => onTriggerCall(contact.id)}
                    className="ml-3 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded hover:bg-blue-200"
                  >
                    Ring nu
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pagination or "View More" button when needed */}
      {contacts.length > 15 && (
        <div className="p-4 border-t bg-gray-50 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            Visa alla {contacts.length} kontakter
          </button>
        </div>
      )}
    </div>
  );
};

export default CallStatusPanel;
