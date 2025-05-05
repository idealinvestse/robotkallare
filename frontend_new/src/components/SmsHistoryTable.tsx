import React, { useState } from 'react';
import { SmsMessage } from '../hooks/useSmsHistory';

interface SmsHistoryTableProps {
  messages: SmsMessage[];
  isLoading: boolean;
  totalCount: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  pageSize: number;
}

/**
 * Komponent för att visa historik över SMS-utskick med filtreringsmöjligheter
 * och expanderbara rader för att visa hela meddelanden
 */
const SmsHistoryTable: React.FC<SmsHistoryTableProps> = ({
  messages,
  isLoading,
  totalCount,
  currentPage,
  onPageChange,
  pageSize
}) => {
  const [expandedMessageId, setExpandedMessageId] = useState<string | null>(null);
  
  // Hjälpfunktion för att formatera datum
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('sv-SE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Skapa statusbadge med rätt färg baserat på status
  const renderStatusBadge = (status: SmsMessage['status']) => {
    const statusStyles = {
      'sent': 'bg-blue-100 text-blue-800 border-blue-200',
      'delivered': 'bg-green-100 text-green-800 border-green-200',
      'failed': 'bg-red-100 text-red-800 border-red-200',
      'queued': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    
    const statusLabels = {
      'sent': 'Skickat',
      'delivered': 'Levererat',
      'failed': 'Misslyckades',
      'queued': 'I kö'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full border ${statusStyles[status]}`}>
        {statusLabels[status]}
      </span>
    );
  };
  
  // Hjälpfunktion för att förkorta långa texter
  const truncateText = (text: string, maxLength: number = 40) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };
  
  const totalPages = Math.ceil(totalCount / pageSize);
  
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">SMS Historik</h3>
        <div className="flex items-center text-sm text-gray-500">
          <span>Visar {messages.length} av {totalCount} meddelanden</span>
        </div>
      </div>
      
      {isLoading ? (
        <div className="p-8 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Laddar SMS-historik...</p>
        </div>
      ) : messages.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <p className="mt-2">Inga SMS-meddelanden hittades</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Meddelande</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Skickat</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Typ</th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Åtgärder</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {messages.map(message => (
                <React.Fragment key={message.id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{message.contactName}</div>
                      <div className="text-sm text-gray-500">{message.phoneNumber}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs">
                        {truncateText(message.message)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTime(message.sentTime)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {renderStatusBadge(message.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {message.messageType === 'template' ? (
                        <span className="inline-flex items-center">
                          <svg className="h-4 w-4 mr-1 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                          </svg>
                          {message.templateName || 'Mall'}
                        </span>
                      ) : (
                        <span className="inline-flex items-center">
                          <svg className="h-4 w-4 mr-1 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Anpassat
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button 
                        onClick={() => setExpandedMessageId(expandedMessageId === message.id ? null : message.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        {expandedMessageId === message.id ? 'Dölj' : 'Visa'}
                      </button>
                    </td>
                  </tr>
                  
                  {/* Expanderad vy för att visa hela meddelandet */}
                  {expandedMessageId === message.id && (
                    <tr className="bg-gray-50">
                      <td colSpan={6} className="px-6 py-4">
                        <div className="text-sm text-gray-600">
                          <div className="mb-4 p-3 bg-white rounded border">
                            <p className="whitespace-pre-wrap">{message.message}</p>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4">
                            {message.campaign && (
                              <div>
                                <p className="font-medium">Kampanj</p>
                                <p className="text-gray-500 text-xs mt-1">{message.campaign.name}</p>
                              </div>
                            )}
                            
                            {message.deliveredTime && (
                              <div>
                                <p className="font-medium">Levererat</p>
                                <p className="text-gray-500 text-xs mt-1">{formatTime(message.deliveredTime)}</p>
                              </div>
                            )}
                          </div>
                          
                          <div className="mt-3 flex space-x-2">
                            <button className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700">
                              Skicka nytt meddelande
                            </button>
                            <button className="px-3 py-1 text-xs bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
                              Kopiera meddelande
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
                <span className="font-medium">{totalCount}</span> meddelanden
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
                
                {/* Sidnummer */}
                {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                  // Beräkna vilka sidnummer som ska visas
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

export default SmsHistoryTable;
