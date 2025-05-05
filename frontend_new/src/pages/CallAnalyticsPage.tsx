import React, { useState } from 'react';
import { useContacts } from '../hooks/useContacts';
import { useCallLogs } from '../hooks/useCallLogs';
import CallStatisticsPanel from '../components/CallStatisticsPanel';
import CallHistoryTable from '../components/CallHistoryTable';

/**
 * Sida för analys av samtalsdata och historik
 * Ger operatören detaljerad insyn i Twilio-samtalens resultat och status
 */
const CallAnalyticsPage: React.FC = () => {
  const { data: contacts, isLoading: contactsLoading } = useContacts();
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 10;
  const { data: callLogsData, isLoading: logsLoading } = useCallLogs(PAGE_SIZE, currentPage);

  if (contactsLoading || logsLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-blue-500"></div>
          <p className="text-lg font-medium text-gray-700">Laddar samtalsdata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Samtalsanalys</h1>
              <p className="mt-1 text-sm text-gray-500">
                Fullständig analys och historik för Twilio-samtal
              </p>
            </div>
            
            <div>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 ml-3">
                Exportera rapport
              </button>
              <button className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 ml-3">
                Nytt utskick
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Statistikkolumn - tar 1/3 av bredden på stora skärmar */}
          <div>
            <CallStatisticsPanel 
              contacts={contacts || []} 
              timeRangeFilter="day" 
            />
            
            {/* Extra panel för snabbfiltrering */}
            <div className="bg-white rounded-lg shadow mt-8 p-4">
              <h3 className="text-lg font-medium mb-4">Snabbfilter</h3>
              <div className="space-y-3">
                <button className="w-full py-2 px-4 rounded-md text-left border bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100">
                  <div className="font-medium">Dagens samtal</div>
                  <div className="text-sm text-blue-600">Senaste 24 timmarna</div>
                </button>
                <button className="w-full py-2 px-4 rounded-md text-left border hover:bg-gray-50 text-gray-700">
                  <div className="font-medium">Samtalsfel</div>
                  <div className="text-sm text-gray-500">Samtal som misslyckades</div>
                </button>
                <button className="w-full py-2 px-4 rounded-md text-left border hover:bg-gray-50 text-gray-700">
                  <div className="font-medium">Samtalsframgång</div>
                  <div className="text-sm text-gray-500">Bekräftade samtal</div>
                </button>
                <button className="w-full py-2 px-4 rounded-md text-left border hover:bg-gray-50 text-gray-700">
                  <div className="font-medium">Senaste veckans samtal</div>
                  <div className="text-sm text-gray-500">Samtal de senaste 7 dagarna</div>
                </button>
              </div>
            </div>
          </div>
          
          {/* Historik-kolumn - tar 2/3 av bredden på stora skärmar */}
          <div className="lg:col-span-2">
            <CallHistoryTable 
              logs={callLogsData?.logs || []}
              isLoading={logsLoading}
              totalCount={callLogsData?.total || 0}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              pageSize={PAGE_SIZE}
            />
            
            {/* Samtalsrekommendationer */}
            <div className="bg-white rounded-lg shadow mt-8 p-4">
              <h3 className="text-lg font-medium mb-4">Rekommendationer</h3>
              <div className="space-y-4">
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-yellow-800">Upptäckte flera missade samtal</h3>
                      <div className="mt-2 text-sm text-yellow-700">
                        <p>5 kontakter har minst 3 missade samtalsförsök. Överväg att prioritera manuell uppföljning.</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">Hög framgångsgrad för morgonsamtal</h3>
                      <div className="mt-2 text-sm text-green-700">
                        <p>Samtal mellan 08:00-10:00 har 78% bekräftelsegrad. Överväg att schemalägga kritiska samtal på morgonen.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CallAnalyticsPage;
