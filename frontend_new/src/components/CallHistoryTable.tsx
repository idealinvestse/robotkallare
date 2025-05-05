import React, { useState } from 'react';
import { CallLog } from '../hooks/useCallLogs';

interface CallHistoryTableProps {
  logs: CallLog[];
  isLoading: boolean;
  totalCount: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  pageSize: number;
}

/**
 * Visar en tabell med samtalshistorik från Twilio
 * Inkluderar filtrering, sortering och paginering
 */
const CallHistoryTable: React.FC<CallHistoryTableProps> = ({
  logs,
  isLoading,
  totalCount,
  currentPage,
  onPageChange,
  pageSize
}) => {
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  
  // Formatera tidsstämpel till läsbar tid
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('sv-SE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  // Formatera samtalslängd från sekunder till läsbar format (mm:ss)
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };
  
  // Generera status-badge med rätt färg baserat på samtalsstatus
  const renderStatusBadge = (status: CallLog['status']) => {
    const statusStyles = {
      'completed': 'bg-green-100 text-green-800 border-green-200',
      'no-answer': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'busy': 'bg-orange-100 text-orange-800 border-orange-200',
      'failed': 'bg-red-100 text-red-800 border-red-200',
      'canceled': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    
    const statusLabels = {
      'completed': 'Genomfört',
      'no-answer': 'Inget svar',
      'busy': 'Upptagen',
      'failed': 'Misslyckades',
      'canceled': 'Avbrutet'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full border ${statusStyles[status]}`}>
        {statusLabels[status]}
      </span>
    );
  };

  // Beräkna paginering
  const totalPages = Math.ceil(totalCount / pageSize);
  
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Samtalshistorik</h3>
        <div className="flex items-center text-sm text-gray-500">
          <span>Visar {logs.length} av {totalCount} samtal</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-8 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Laddar samtalshistorik...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <p className="mt-2">Inga samtalsloggar hittades</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Telefon</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Starttid</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Längd</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inspelning</th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Åtgärder</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map(log => (
                <React.Fragment key={log.id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{log.contactName}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.phoneNumber}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTime(log.startTime)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDuration(log.duration)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {renderStatusBadge(log.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.recordingUrl ? (
                        <button className="text-blue-600 hover:text-blue-800">
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                      ) : (
                        <span>-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button 
                        onClick={() => setExpandedLogId(expandedLogId === log.id ? null : log.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        {expandedLogId === log.id ? 'Dölj detaljer' : 'Visa detaljer'}
                      </button>
                    </td>
                  </tr>
                  
                  {/* Expanderbar detaljevy */}
                  {expandedLogId === log.id && (
                    <tr className="bg-gray-50">
                      <td colSpan={7} className="px-6 py-4">
                        <div className="text-sm text-gray-600">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="font-medium">Twilio Call SID</p>
                              <p className="text-gray-500 text-xs mt-1 font-mono">{log.callSid}</p>
                            </div>
                            <div>
                              <p className="font-medium">Samtalsperiod</p>
                              <p className="text-gray-500 text-xs mt-1">
                                {formatTime(log.startTime)} → {log.endTime ? formatTime(log.endTime) : 'Ej avslutad'}
                              </p>
                            </div>
                            
                            {log.notes && (
                              <div className="col-span-2">
                                <p className="font-medium">Anteckningar</p>
                                <p className="text-gray-500 text-xs mt-1">{log.notes}</p>
                              </div>
                            )}
                          </div>
                          
                          <div className="mt-4 flex space-x-2">
                            <button className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700">
                              Ring kontakt igen
                            </button>
                            <button className="px-3 py-1 text-xs bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
                              Lägg till anteckning
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginering */}
      {totalPages > 1 && (
        <div className="px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Visar <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> till <span className="font-medium">{Math.min(currentPage * pageSize, totalCount)}</span> av{' '}
                <span className="font-medium">{totalCount}</span> samtal
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  disabled={currentPage === 1}
                  onClick={() => onPageChange(currentPage - 1)}
                  className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <span className="sr-only">Föregående</span>
                  &laquo;
                </button>
                
                {/* Page numbers */}
                {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                  // Calculate page numbers to show (simplified for brevity)
                  let pageNum = i + 1;
                  if (totalPages > 5 && currentPage > 3) {
                    pageNum = currentPage - 2 + i;
                  }
                  if (pageNum > totalPages) return null;
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => onPageChange(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium ${
                        currentPage === pageNum ? 'text-blue-600 z-10 border-blue-500' : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                
                <button
                  disabled={currentPage === totalPages}
                  onClick={() => onPageChange(currentPage + 1)}
                  className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <span className="sr-only">Nästa</span>
                  &raquo;
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CallHistoryTable;
