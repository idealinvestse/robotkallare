import React, { useState } from 'react';
import Button from '../ui/Button'; // Assuming Button is in ui folder
import { ContactStatus } from '../../types/operator'; // Make sure ContactStatus is imported

interface ContactCardProps {
  id: string;
  name: string;
  primaryPhone: string;
  status: ContactStatus;
  nextAttemptTime?: string; // ISO string or similar
  onManualCall: (id: string) => void;
  onUpdateStatus: (newStatus: ContactStatus) => void; // Prop to update status generally
  onConfirm: (id: string) => void; // Kept specific for now, can be refactored later
  onPostpone: (id: string, delayMinutes: number) => void;
}

// Helper to get styling based on status
const getStatusStyle = (status: ContactStatus): { chip: string; border: string } => {
  switch (status) {
    case 'CONFIRMED':
      return { chip: 'bg-green-100 text-green-800', border: 'border-green-500' };
    case 'RINGING_PRIMARY':
    case 'RINGING_SECONDARY':
    case 'SCHEDULED':
    case 'PENDING':
      return { chip: 'bg-blue-100 text-blue-800', border: 'border-blue-500' };
    case 'NO_ANSWER':
    case 'MANUAL_NEEDED':
      return { chip: 'bg-yellow-100 text-yellow-800', border: 'border-yellow-500' };
    case 'ERROR':
      return { chip: 'bg-red-100 text-red-800', border: 'border-red-500' };
    default:
      return { chip: 'bg-gray-100 text-gray-800', border: 'border-gray-300' };
  }
};

// Helper to format status text
const formatStatus = (status: ContactStatus): string => {
  switch (status) {
    case 'RINGING_PRIMARY': return 'Ringing (Primary)';
    case 'RINGING_SECONDARY': return 'Ringing (Secondary)';
    case 'NO_ANSWER': return 'No Answer';
    case 'MANUAL_NEEDED': return 'Manual Action';
    case 'CONFIRMED': return 'Confirmed';
    case 'SCHEDULED': return 'Scheduled';
    default: return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
  }
}

const ContactCard: React.FC<ContactCardProps> = ({
  id,
  name,
  primaryPhone,
  status,
  nextAttemptTime,
  onManualCall,
  onUpdateStatus,
  onConfirm,
  onPostpone,
}) => {
  const { chip: chipStyle, border: borderStyle } = getStatusStyle(status);
  const [showPostpone, setShowPostpone] = useState(false);

  return (
    <div className={`p-3 border rounded-md bg-white shadow-sm mb-2 ${borderStyle}`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className="font-semibold text-gray-900">{name}</p>
          <p className="text-sm text-gray-600">{primaryPhone}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${chipStyle}`}>
          {formatStatus(status)}
        </span>
      </div>

      {nextAttemptTime && (status === 'SCHEDULED' || status === 'NO_ANSWER') && (
        <p className="text-xs text-gray-500 mb-2">
          Next attempt: {new Date(nextAttemptTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      )}

      {/* Action Buttons - enabled based on status */}
      {status !== 'CONFIRMED' && (
        <div className="mt-4 flex flex-wrap gap-2 justify-end">
          {/* Confirm Action: Typically after No Answer */}
          {status === 'NO_ANSWER' && (
            <Button variant="outline" size="sm" onClick={() => onConfirm(id)}>Confirm</Button>
          )}

          {/* Manual Call: Useful for No Answer, Manual Needed, Error */}
          {(status === 'NO_ANSWER' || status === 'MANUAL_NEEDED' || status === 'ERROR') && (
            <Button variant="outline" size="sm" onClick={() => onManualCall(id)}>Call Manually</Button>
          )}

          {/* Mark Error: Primarily for Manual Needed status */}
          {status === 'MANUAL_NEEDED' && (
            <Button variant="destructive" size="sm" onClick={() => onUpdateStatus('ERROR')}>Mark Error</Button>
          )}

          {/* Postpone Action: For Pending, Scheduled, No Answer */}
          {(status === 'PENDING' || status === 'SCHEDULED' || status === 'NO_ANSWER') && !showPostpone && (
            <Button variant="ghost" size="sm" onClick={() => setShowPostpone(true)}>Postpone...</Button>
          )}

          {/* Postpone Options (Shown when postpone button clicked) */}
          {showPostpone && (
            <div className="flex items-center gap-1 p-1 border rounded-md bg-gray-50 dark:bg-gray-700">
              {[5, 15, 30].map((delay) => (
                <Button
                  key={delay}
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => { onPostpone(id, delay); setShowPostpone(false); }}
                >
                  {delay}m
                </Button>
              ))}
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900"
                onClick={() => setShowPostpone(false)}
              >
                X
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContactCard;
