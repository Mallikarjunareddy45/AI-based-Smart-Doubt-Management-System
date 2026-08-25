import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Direct Access Route Guard
export const ProtectedRoute: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return <Outlet />;
};

// Role Guard allowing direct access to all roles
interface RoleGuardProps {
  allowedRoles: ('student' | 'tutor' | 'admin')[];
}

export const RoleGuard = ({ allowedRoles }: RoleGuardProps) => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return <Outlet />;
};

// Default Landing Redirect logic
export const DashboardRedirect: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  return <Navigate to="/student" replace />;
};

