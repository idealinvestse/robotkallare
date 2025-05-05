import { create } from 'zustand';
import { Group, ContactStatus, Contact } from '../types/operator';

// Mock Data - To be replaced by API calls
const initialMockGroups: Group[] = [
  {
    id: 'group1',
    name: 'Emergency Response Team A',
    contacts: [
      { id: 'c1', name: 'Alice Johnson', primaryPhone: '555-1234', status: 'CONFIRMED' },
      { id: 'c2', name: 'Bob Williams', primaryPhone: '555-5678', status: 'RINGING_SECONDARY' },
      { id: 'c3', name: 'Charlie Brown', primaryPhone: '555-9012', status: 'MANUAL_NEEDED', nextAttemptTime: new Date(Date.now() + 10 * 60000).toISOString() },
    ],
  },
  {
    id: 'group2',
    name: 'Building Supervisors',
    contacts: [
      { id: 'c4', name: 'Diana Prince', primaryPhone: '555-1122', status: 'CONFIRMED' },
      { id: 'c5', name: 'Ethan Hunt', primaryPhone: '555-3344', status: 'CONFIRMED' },
      { id: 'c6', name: 'Fiona Gallagher', primaryPhone: '555-5566', status: 'NO_ANSWER', nextAttemptTime: new Date(Date.now() + 5 * 60000).toISOString() },
      { id: 'c7', name: 'George Costanza', primaryPhone: '555-7788', status: 'PENDING' },
    ],
  },
  {
    id: 'group3',
    name: 'Floor Wardens',
    contacts: [
      { id: 'c8', name: 'Hannah Montana', primaryPhone: '555-1010', status: 'CONFIRMED' },
      { id: 'c9', name: 'Isaac Newton', primaryPhone: '555-2020', status: 'CONFIRMED' },
      { id: 'c10', name: 'Jackie Chan', primaryPhone: '555-3030', status: 'CONFIRMED' },
    ]
  }
];

// --- Selectors --- 
// We define selectors outside the create function for better organization and potential memoization later.

// Define priority order for sorting
const statusPriority: Record<ContactStatus, number> = {
  'ERROR': 1,
  'MANUAL_NEEDED': 2,
  'NO_ANSWER': 3,
  'RINGING_PRIMARY': 4,
  'RINGING_SECONDARY': 5,
  'PENDING': 6,
  'SCHEDULED': 7,
  'CONFIRMED': 99 // Lowest priority, should be filtered out anyway
};

const selectActionableContacts = (state: OperatorState): Contact[] => {
  const actionableStatuses: ContactStatus[] = [
    'PENDING', 'SCHEDULED', 'RINGING_PRIMARY', 'RINGING_SECONDARY', 
    'NO_ANSWER', 'MANUAL_NEEDED', 'ERROR'
  ];
  return state.groups.flatMap(group => 
    group.contacts.filter(contact => actionableStatuses.includes(contact.status))
  )
  .sort((a, b) => statusPriority[a.status] - statusPriority[b.status]);
}

interface OperatorState {
  groups: Group[];
  isLoading: boolean;
  error: string | null;
  showAllContacts: boolean; // Added state for toggling view
  // Actions
  fetchGroups: () => Promise<void>; // Placeholder for API call
  updateContactStatus: (contactId: string, newStatus: ContactStatus) => void;
  toggleShowAllContacts: () => void; // Action to toggle the view
  // TODO: Add actions for bulk updates, manual calls, postpone etc.
}

export const useOperatorStore = create<OperatorState>((set) => ({
  groups: initialMockGroups, // Initialize with mock data
  isLoading: false,
  error: null,
  showAllContacts: false, // Default state

  // --- Actions --- 

  // Placeholder action to fetch groups (will replace mock data)
  fetchGroups: async () => {
    set({ isLoading: true, error: null });
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/operator/groups'); // Example endpoint
      // if (!response.ok) throw new Error('Failed to fetch groups');
      // const data: Group[] = await response.json();
      // set({ groups: data, isLoading: false });
      console.warn('fetchGroups not implemented, using mock data.');
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500)); 
      set({ groups: initialMockGroups, isLoading: false }); // Resetting with mock for now
    } catch (error: any) {
      console.error('Error fetching groups:', error);
      set({ error: error.message || 'Failed to fetch groups', isLoading: false });
    }
  },

  // Action to update a single contact's status
  updateContactStatus: (contactId, newStatus) =>
    set((state) => ({
      groups: state.groups.map(group => ({
        ...group,
        contacts: group.contacts.map(contact => 
          contact.id === contactId ? { ...contact, status: newStatus } : contact
        )
      }))
    })),

  // Action to toggle the display mode
  toggleShowAllContacts: () => 
    set((state) => ({ showAllContacts: !state.showAllContacts })),
}));

// Export the selector separately or make it part of the returned state if preferred.
// For simplicity now, components can import and use it directly with the store hook:
// const actionableContacts = useOperatorStore(selectActionableContacts);
export { selectActionableContacts };
