import React from 'react';
import { useContacts } from '../hooks/useContacts';
import { useGroups } from '../hooks/useGroups';

const OperatorDashboard: React.FC = () => {
  const { data: contacts, isLoading: contactsLoading, error: contactsError } = useContacts();
  const { data: groups, isLoading: groupsLoading, error: groupsError } = useGroups();

  if (contactsLoading || groupsLoading) {
    return <div className="p-6">Loading contacts and groups...</div>;
  }
  if (contactsError || groupsError) {
    return <div className="p-6 text-red-600">Error loading data: {contactsError?.message || groupsError?.message}</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Operator Dashboard</h1>
      <div className="mb-4">
        <span className="font-semibold">Total contacts:</span> {contacts?.length ?? 0}
      </div>
      <div className="mb-4">
        <span className="font-semibold">Total groups:</span> {groups?.length ?? 0}
      </div>
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Contacts</h2>
        <ul className="list-disc ml-6">
          {contacts && contacts.length > 0 ? contacts.map(c => (
            <li key={c.id}>{c.name} ({c.primaryPhone})</li>
          )) : <li>No contacts found.</li>}
        </ul>
      </div>
      <div>
        <h2 className="text-lg font-semibold">Groups</h2>
        <ul className="list-disc ml-6">
          {groups && groups.length > 0 ? groups.map(g => (
            <li key={g.id}>{g.name}</li>
          )) : <li>No groups found.</li>}
        </ul>
      </div>
    </div>
  );
};

export default OperatorDashboard;
