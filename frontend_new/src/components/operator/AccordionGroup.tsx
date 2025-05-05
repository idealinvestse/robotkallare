import React, { useState } from 'react';
import { ChevronDownIcon } from 'lucide-react';

interface AccordionGroupProps {
  groupName: string;
  completedCount: number;
  totalCount: number;
  children: React.ReactNode;
}

const AccordionGroup: React.FC<AccordionGroupProps> = ({ groupName, completedCount, totalCount, children }) => {
  const [isOpen, setIsOpen] = useState(true);

  const percentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const getStatusColor = (perc: number): string => {
    if (perc >= 95) return 'bg-green-500';
    if (perc >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const statusColor = getStatusColor(percentage);

  return (
    <div className="border border-gray-200 rounded-md mb-4 bg-white shadow-sm">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 text-left focus:outline-none focus-visible:ring focus-visible:ring-blue-500 focus-visible:ring-opacity-75"
        aria-expanded={isOpen}
      >
        <div className="flex items-center space-x-3">
          <span className={`w-3 h-3 rounded-full ${statusColor}`}></span>
          <span className="font-medium text-gray-800">{groupName}</span>
          <span className="text-sm text-gray-500">({completedCount}/{totalCount})</span>
        </div>
        <div className="flex items-center space-x-2">
          {/* Progress Bar */}
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${statusColor}`}
              style={{ width: `${percentage}%` }}
            ></div>
          </div>
          <ChevronDownIcon
            className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`}
          />
        </div>
      </button>

      {/* Content */}
      {isOpen && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          {children}
        </div>
      )}
    </div>
  );
};

export default AccordionGroup;
