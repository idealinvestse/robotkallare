import React from 'react';
import { Outlet } from 'react-router-dom';
import MainNavigation from './MainNavigation';

/**
 * Huvudlayout för applikationen
 * Innehåller navigation och plats för sidors innehåll (via Outlet)
 */
const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <MainNavigation />
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
