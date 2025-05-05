import React from 'react';
import { Contact, ContactStatus } from '../types/operator';

interface CallStatisticsPanelProps {
  contacts: Contact[];
  timeRangeFilter?: 'day' | 'week' | 'month' | 'all';
}

/**
 * Statistikpanel för samtalsdata från Twilio
 * Visar trender, framgångsgrad och fördelning av samtalsstatus
 */
const CallStatisticsPanel: React.FC<CallStatisticsPanelProps> = ({
  contacts,
  timeRangeFilter = 'day'
}) => {
  // 1. Beräkna grundläggande statistik
  const totalContacts = contacts.length;
  if (totalContacts === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4 text-center text-gray-500">
        Ingen samtalsdata tillgänglig för statistikanalys.
      </div>
    );
  }

  // Gruppera kontakter efter status
  const statusCounts: Record<ContactStatus, number> = {
    'PENDING': 0,
    'SCHEDULED': 0,
    'RINGING_PRIMARY': 0,
    'RINGING_SECONDARY': 0,
    'NO_ANSWER': 0,
    'CONFIRMED': 0,
    'MANUAL_NEEDED': 0,
    'ERROR': 0
  };

  // Räkna status
  contacts.forEach(contact => {
    statusCounts[contact.status]++;
  });

  // Beräkna statistik
  const confirmedCount = statusCounts.CONFIRMED;
  const successRate = Math.round((confirmedCount / totalContacts) * 100);
  
  const needAttentionCount = statusCounts.NO_ANSWER + statusCounts.MANUAL_NEEDED + statusCounts.ERROR;
  const attentionRate = Math.round((needAttentionCount / totalContacts) * 100);
  
  const inProgressCount = statusCounts.RINGING_PRIMARY + statusCounts.RINGING_SECONDARY;
  const waitingCount = statusCounts.PENDING + statusCounts.SCHEDULED;

  // Beräkna tidsbaserad uppdelning (för trendlinjen)
  // Simulerar historiska data - i en riktig implementation skulle detta hämtas från API
  const timeData = {
    labels: ['08:00', '10:00', '12:00', '14:00', '16:00'],
    confirmed: [5, 12, 25, 38, confirmedCount],
    attempted: [10, 25, 45, 70, totalContacts - waitingCount]
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">Samtalsstatistik</h3>
          <div className="flex space-x-1 bg-gray-100 rounded-md p-1 text-sm">
            <button className={`px-3 py-1 rounded-md ${timeRangeFilter === 'day' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600'}`}>
              Idag
            </button>
            <button className={`px-3 py-1 rounded-md ${timeRangeFilter === 'week' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600'}`}>
              Vecka
            </button>
            <button className={`px-3 py-1 rounded-md ${timeRangeFilter === 'month' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600'}`}>
              Månad
            </button>
          </div>
        </div>
      </div>

      {/* Huvudstatistikkort */}
      <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-gray-50 p-3 rounded-lg border">
          <div className="text-sm text-gray-500">Totalt</div>
          <div className="mt-1 text-2xl font-semibold">{totalContacts}</div>
          <div className="text-xs text-gray-500">kontakter</div>
        </div>

        <div className="bg-gray-50 p-3 rounded-lg border">
          <div className="text-sm text-gray-500">Bekräftade</div>
          <div className="mt-1 text-2xl font-semibold text-green-600">{confirmedCount}</div>
          <div className="text-xs text-gray-500">{successRate}% av totalt</div>
        </div>

        <div className="bg-gray-50 p-3 rounded-lg border">
          <div className="text-sm text-gray-500">Behöver åtgärd</div>
          <div className="mt-1 text-2xl font-semibold text-yellow-600">{needAttentionCount}</div>
          <div className="text-xs text-gray-500">{attentionRate}% av totalt</div>
        </div>

        <div className="bg-gray-50 p-3 rounded-lg border">
          <div className="text-sm text-gray-500">Aktiva samtal</div>
          <div className="mt-1 text-2xl font-semibold text-blue-600">{inProgressCount}</div>
          <div className="text-xs text-gray-500">just nu</div>
        </div>
      </div>

      {/* Samtalstrend - Grafisk visning med responsiv SVG */}
      <div className="p-4 border-t">
        <h4 className="text-sm font-medium text-gray-700 mb-4">Samtalstrend</h4>
        <div className="h-40 relative">
          {/* Enkel SVG-baserad graf för samtalstrend */}
          <svg className="w-full h-full" viewBox="0 0 500 150" preserveAspectRatio="none">
            {/* Grid lines */}
            <line x1="0" y1="0" x2="500" y2="0" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="50" x2="500" y2="50" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="100" x2="500" y2="100" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="150" x2="500" y2="150" stroke="#e5e7eb" strokeWidth="1" />
            
            {/* Attempted calls line */}
            <polyline
              points="0,130 125,110 250,80 375,40 500,30"
              fill="none"
              stroke="#93c5fd"
              strokeWidth="2"
            />
            
            {/* Confirmed calls line */}
            <polyline
              points="0,140 125,125 250,110 375,80 500,60"
              fill="none"
              stroke="#34d399"
              strokeWidth="2"
            />

            {/* Area under confirmed line */}
            <polygon
              points="0,150 0,140 125,125 250,110 375,80 500,60 500,150"
              fill="#d1fae5"
              fillOpacity="0.5"
            />
          </svg>

          {/* Legend */}
          <div className="absolute bottom-0 left-0 flex space-x-4 text-xs">
            <div className="flex items-center">
              <span className="block w-3 h-3 bg-blue-400 mr-1"></span>
              <span>Uppringda</span>
            </div>
            <div className="flex items-center">
              <span className="block w-3 h-3 bg-green-400 mr-1"></span>
              <span>Bekräftade</span>
            </div>
          </div>

          {/* X-axis labels */}
          <div className="absolute bottom-6 left-0 w-full flex justify-between text-xs text-gray-500">
            {timeData.labels.map((label, index) => (
              <div key={index} style={{ left: `${index * 25}%` }}>{label}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Statusfördelning */}
      <div className="p-4 border-t">
        <h4 className="text-sm font-medium text-gray-700 mb-4">Statusfördelning</h4>
        <div className="space-y-3">
          {/* CONFIRMED status */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Bekräftade</span>
              <span>{successRate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full" 
                style={{ width: `${successRate}%` }}
              ></div>
            </div>
          </div>
          
          {/* PENDING + SCHEDULED status */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Väntande/Schemalagda</span>
              <span>{Math.round((waitingCount / totalContacts) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gray-500 h-2 rounded-full" 
                style={{ width: `${Math.round((waitingCount / totalContacts) * 100)}%` }}
              ></div>
            </div>
          </div>
          
          {/* RINGING status */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Pågående samtal</span>
              <span>{Math.round((inProgressCount / totalContacts) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full" 
                style={{ width: `${Math.round((inProgressCount / totalContacts) * 100)}%` }}
              ></div>
            </div>
          </div>
          
          {/* Need attention */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Kräver åtgärd</span>
              <span>{attentionRate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-yellow-500 h-2 rounded-full" 
                style={{ width: `${attentionRate}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottenknapp för detaljrapport */}
      <div className="p-4 border-t bg-gray-50 text-center">
        <button className="text-sm text-blue-600 font-medium">
          Visa fullständig samtalsrapport
        </button>
      </div>
    </div>
  );
};

export default CallStatisticsPanel;
