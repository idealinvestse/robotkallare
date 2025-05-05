import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const MainNavigation: React.FC = () => {
  const { logout } = useAuth();
  const location = useLocation();
  
  // Aktiv länk styling
  const getNavLinkClass = (path: string) => {
    const baseClass = "flex items-center px-4 py-2 text-sm font-medium rounded-md";
    return location.pathname === path
      ? `${baseClass} bg-gray-100 text-blue-600`
      : `${baseClass} text-gray-600 hover:bg-gray-50 hover:text-gray-900`;
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              {/* Logotyp */}
              <Link to="/" className="text-blue-600 font-bold text-xl flex items-center">
                <svg className="w-8 h-8 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="fill-blue-600 stroke-blue-600" />
                </svg>
                GDial
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {/* Huvudnavigation */}
              <Link to="/" className={getNavLinkClass("/")}>
                <svg className="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7m-7-7v14" />
                </svg>
                Dashboard
              </Link>
              <Link to="/call-analytics" className={getNavLinkClass("/call-analytics")}>
                <svg className="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Samtalsanalys
              </Link>
              <Link to="/communication-history" className={getNavLinkClass("/communication-history")}>
                <svg className="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                </svg>
                Kommunikationshistorik
              </Link>
              <Link to="/outbox" className={getNavLinkClass("/outbox")}>
                <svg className="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
                </svg>
                Utskick
              </Link>
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {/* Snabbknappar och användarinfo */}
            <button
              type="button"
              className="px-2 py-1 mr-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Nytt utskick
            </button>

            {/* Dropdown-meny för användarinställningar */}
            <div className="relative">
              <button
                type="button"
                className="flex items-center text-gray-700 hover:text-gray-900 focus:outline-none"
              >
                <span className="sr-only">Öppna användarmeny</span>
                <img
                  className="h-8 w-8 rounded-full bg-gray-200 p-1"
                  src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' /%3E%3C/svg%3E"
                  alt="User avatar"
                />
                <span className="ml-2 text-sm font-medium">Operatör</span>
              </button>
              
              {/* Utloggning direkt från navigation */}
              <button 
                onClick={() => logout()}
                className="ml-3 px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Logga ut
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default MainNavigation;
