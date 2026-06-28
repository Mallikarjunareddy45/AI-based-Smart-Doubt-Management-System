import React from 'react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="flex h-screen w-screen bg-[#f8fafc] overflow-hidden">
      {/* Fixed Sidebar navigation */}
      <Sidebar />

      {/* Main viewport */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Sticky top navbar */}
        <Navbar />

        {/* Scrollable content container */}
        <main className="flex-1 overflow-y-auto p-8 page-transit">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
export default Layout;
