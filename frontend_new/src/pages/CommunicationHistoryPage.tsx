import React, { useState } from 'react';
import { useCallLogs } from '../hooks/useCallLogs';
import { useSmsHistory, useSmsStats } from '../hooks/useSmsHistory';
import CallHistoryTable from '../components/CallHistoryTable';
import SmsHistoryTable from '../components/SmsHistoryTable';


/**
 * Sida för komplett kommunikationshistorik (samtal + SMS)
 * Ger operatören en fullständig översikt över all kontakt
 */
const CommunicationHistoryPage: React.FC = () => {
  // State för filtrering och paginering
  const [activeTab, setActiveTab] = useState<'calls' | 'sms'>('calls');
  const [callsPage, setCallsPage] = useState(1);
  const [smsPage, setSmsPage] = useState(1);
  const PAGE_SIZE = 10;
  
  // Filter state
  const [filters, setFilters] = useState<{
    contactId?: string;
    campaignId?: string;
    status?: 'sent' | 'delivered' | 'failed' | 'queued' | '';
    startDate?: string;
    endDate?: string;
    search?: string;
  }>({
    contactId: '',
    campaignId: '',
    status: '',
    startDate: '',
    endDate: '',
    search: ''
  });

  // Förarbeta filters för att ta bort tomma strängar innan API-anrop
  const processedFilters = {
    ...(filters.contactId ? { contactId: filters.contactId } : {}),
    ...(filters.campaignId ? { campaignId: filters.campaignId } : {}),
    // Hantera status-fältet speciellt för att undvika typfel
    ...((filters.status && ['sent', 'delivered', 'failed', 'queued'].includes(filters.status as string)) 
      ? { status: filters.status as 'sent' | 'delivered' | 'failed' | 'queued' } 
      : {}),
    ...(filters.startDate ? { startDate: filters.startDate } : {}),
    ...(filters.endDate ? { endDate: filters.endDate } : {}),
    ...(filters.search ? { search: filters.search } : {})
  };

  // API hooks för att hämta data
  const { data: callLogsData, isLoading: callLogsLoading } = useCallLogs(PAGE_SIZE, callsPage);
  const { data: smsData, isLoading: smsLoading } = useSmsHistory(smsPage, PAGE_SIZE, processedFilters);
  const { data: smsStatsData, isLoading: statsLoading } = useSmsStats('day');
  
  // Hantera filterändringar
  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };
  
  // Hantera sökning
  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Filter-logik implementeras här - nuvarande filter används redan i API-anrop
  };
  
  // Render filter panel
  const renderFilterPanel = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <h3 className="text-lg font-medium mb-4">Filter</h3>
      
      <form onSubmit={handleSearch}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Sök</label>
            <input
              type="text"
              id="search"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder="Namn, telefon eller innehåll..."
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              id="status"
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Alla statusar</option>
              {activeTab === 'calls' ? (
                <>
                  <option value="completed">Genomförda</option>
                  <option value="no-answer">Inget svar</option>
                  <option value="failed">Misslyckade</option>
                </>
              ) : (
                <>
                  <option value="delivered">Levererade</option>
                  <option value="sent">Skickade</option>
                  <option value="failed">Misslyckade</option>
                </>
              )}
            </select>
          </div>
          
          <div>
            <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700 mb-1">Datumintervall</label>
            <div className="flex space-x-2">
              <input
                type="date"
                name="startDate"
                value={filters.startDate}
                onChange={handleFilterChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <span className="flex items-center text-gray-500">till</span>
              <input
                type="date"
                name="endDate"
                value={filters.endDate}
                onChange={handleFilterChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
        
        <div className="flex justify-end space-x-2">
          <button
            type="button"
            onClick={() => setFilters({
              contactId: '',
              campaignId: '',
              status: '',
              startDate: '',
              endDate: '',
              search: ''
            })}
            className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Rensa filter
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            Filtrera
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Kommunikationshistorik</h1>
              <p className="mt-1 text-sm text-gray-500">
                Fullständig historik för samtal och SMS-utskick
              </p>
            </div>
            
            <div>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 ml-3">
                Exportera
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
          {/* Huvudkolumn för historik */}
          <div className="lg:col-span-2">
            {renderFilterPanel()}
            
            {/* Huvudtabeller med tabs för att växla mellan samtal och SMS */}
            <div className="bg-white rounded-lg shadow">
              <div className="border-b">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('calls')}
                    className={`py-4 px-6 text-sm font-medium border-b-2 ${
                      activeTab === 'calls'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Samtal
                  </button>
                  <button
                    onClick={() => setActiveTab('sms')}
                    className={`py-4 px-6 ml-8 text-sm font-medium border-b-2 ${
                      activeTab === 'sms'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    SMS
                  </button>
                </nav>
              </div>
              
              <div className="p-4">
                {activeTab === 'calls' ? (
                  <CallHistoryTable
                    logs={callLogsData?.logs || []}
                    isLoading={callLogsLoading}
                    totalCount={callLogsData?.total || 0}
                    currentPage={callsPage}
                    onPageChange={setCallsPage}
                    pageSize={PAGE_SIZE}
                  />
                ) : (
                  <SmsHistoryTable
                    messages={smsData?.messages || []}
                    isLoading={smsLoading}
                    totalCount={smsData?.total || 0}
                    currentPage={smsPage}
                    onPageChange={setSmsPage}
                    pageSize={PAGE_SIZE}
                  />
                )}
              </div>
            </div>
          </div>
          
          {/* Sidokolumn med realtidsövervakning och snabbstatistik */}
          <div>
            
            {/* SMS Statistik */}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <h3 className="text-lg font-medium mb-4">SMS-statistik</h3>
              
              {statsLoading ? (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-gray-50 border">
                      <div className="text-sm text-gray-500">Totalt skickade</div>
                      <div className="mt-1 text-xl font-semibold">{smsStatsData?.total || 0}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-gray-50 border">
                      <div className="text-sm text-gray-500">Levererade</div>
                      <div className="mt-1 text-xl font-semibold text-green-600">{smsStatsData?.delivered || 0}</div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">Leveransgrad</span>
                      <span className="font-medium">{smsStatsData?.successRate || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{ width: `${smsStatsData?.successRate || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Snabbknappar för kommunikation */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-medium mb-4">Snabbåtgärder</h3>
              
              <div className="space-y-3">
                <button className="w-full py-2 text-left px-4 border rounded-md hover:bg-gray-50 flex items-center">
                  <svg className="w-5 h-5 mr-3 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 3h5m0 0v5m0-5l-6 6M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" />
                  </svg>
                  Skicka samtalsmall
                </button>
                
                <button className="w-full py-2 text-left px-4 border rounded-md hover:bg-gray-50 flex items-center">
                  <svg className="w-5 h-5 mr-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  Skicka SMS-mall
                </button>
                
                <button className="w-full py-2 text-left px-4 border rounded-md hover:bg-gray-50 flex items-center">
                  <svg className="w-5 h-5 mr-3 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  Se kampanjrapport
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunicationHistoryPage;
