import React, { useState } from 'react';
import { useContacts } from '../hooks/useContacts';
import { useGroups } from '../hooks/useGroups';
import { ContactStatus, Contact } from '../types/operator';

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
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<ContactStatus | 'ALL'>('ALL');
  const [groupFilter, setGroupFilter] = useState<string>('ALL');

  // Loading states
  if (contactsLoading || groupsLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-blue-500"></div>
          <p className="text-lg font-medium text-gray-700">Laddar kontakter och grupper...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (contactsError || groupsError) {
    return (
      <div className="m-6 rounded-lg bg-red-50 p-4 text-red-800 shadow-sm">
        <h3 className="mb-2 font-bold">Ett fel uppstod</h3>
        <p>{contactsError?.message || groupsError?.message}</p>
        <button 
          className="mt-4 rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          onClick={() => window.location.reload()}
        >
          Försök igen
        </button>
      </div>
    );
  }

  // Calculate stats
  const totalContacts = contacts?.length || 0;
  const confirmedContacts = contacts?.filter(c => c.status === 'CONFIRMED').length || 0;
  const pendingContacts = contacts?.filter(c => ['PENDING', 'SCHEDULED'].includes(c.status)).length || 0;
  const actionableContacts = contacts?.filter(c => ['NO_ANSWER', 'MANUAL_NEEDED', 'ERROR'].includes(c.status)).length || 0;
  const progressPercentage = totalContacts > 0 ? Math.round((confirmedContacts / totalContacts) * 100) : 0;

  // Filter and search logic
  const filteredContacts = contacts?.filter(contact => {
    // Status filter
    if (statusFilter !== 'ALL' && contact.status !== statusFilter) return false;
    
    // Search term
    if (searchTerm && !contact.name.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !contact.primaryPhone.includes(searchTerm)) return false;
    
    // Group filter - would need proper group-contact relationships
    // This is a placeholder - actual implementation would depend on data structure
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Stats Header */}
      <div className="bg-white p-6 shadow-sm">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Operatörspanel</h1>
        
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Totalt antal kontakter</h3>
            <p className="text-2xl font-bold text-gray-900">{totalContacts}</p>
          </div>
          
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Bekräftade</h3>
            <p className="text-2xl font-bold text-green-600">{confirmedContacts}</p>
          </div>
          
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Väntande</h3>
            <p className="text-2xl font-bold text-blue-600">{pendingContacts}</p>
          </div>
          
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Behöver åtgärd</h3>
            <p className="text-2xl font-bold text-yellow-600">{actionableContacts}</p>
          </div>
        </div>

        <div className="mb-4 h-4 overflow-hidden rounded-full bg-gray-200">
          <div 
            className="h-full bg-green-500 transition-all duration-500" 
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600">{progressPercentage}% bekräftade</p>
      </div>

      {/* Filters and Search */}
      <div className="border-b bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          <div className="w-full md:w-64">
            <label htmlFor="search" className="sr-only">Sök</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                id="search"
                type="search"
                className="block w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-3 text-sm"
                placeholder="Sök på namn eller telefon..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label htmlFor="status-filter" className="mr-2 text-sm font-medium text-gray-700">Status:</label>
            <select
              id="status-filter"
              className="rounded-lg border border-gray-300 bg-white py-1.5 pl-3 pr-7 text-sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ContactStatus | 'ALL')}
            >
              <option value="ALL">Alla</option>
              <option value="CONFIRMED">Bekräftade</option>
              <option value="PENDING">Väntande</option>
              <option value="SCHEDULED">Schemalagda</option>
              <option value="NO_ANSWER">Inget svar</option>
              <option value="MANUAL_NEEDED">Manuell åtgärd</option>
              <option value="ERROR">Fel</option>
            </select>
          </div>

          <div>
            <label htmlFor="group-filter" className="mr-2 text-sm font-medium text-gray-700">Grupp:</label>
            <select
              id="group-filter"
              className="rounded-lg border border-gray-300 bg-white py-1.5 pl-3 pr-7 text-sm"
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
            >
              <option value="ALL">Alla grupper</option>
              {groups?.map(group => (
                <option key={group.id} value={group.id}>{group.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Contact List */}
      <div className="m-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Kontakter</h2>
          <p className="text-sm text-gray-600">Visar {filteredContacts?.length || 0} av {totalContacts} kontakter</p>
        </div>

        {/* Table - optimized for large lists */}
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Namn</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Telefon</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Senaste försök</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Åtgärder</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {filteredContacts && filteredContacts.length > 0 ? (
                filteredContacts.map((contact) => (
                  <tr key={contact.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="font-medium text-gray-900">{contact.name}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{contact.primaryPhone}</td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={contact.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {contact.lastAttemptTime ? 
                        new Date(contact.lastAttemptTime).toLocaleString('sv-SE', {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit'
                        }) : 'Ej kontaktad'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                      <button className="mr-2 rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700">Ring</button>
                      <button className="rounded bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200">Mer</button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    {searchTerm || statusFilter !== 'ALL' ? 
                      'Inga kontakter matchade sökningen.' : 
                      'Inga kontakter hittades.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination placeholder */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            <span>Sida 1 av 1</span>
          </div>
          <div className="flex space-x-2">
            <button 
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              disabled={true}
            >
              Föregående
            </button>
            <button 
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              disabled={true}
            >
              Nästa
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OperatorDashboard;
