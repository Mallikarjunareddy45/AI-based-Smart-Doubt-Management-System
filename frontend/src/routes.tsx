import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Protected Route Guard to verify user is authenticated
export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

// Role Guard to restrict page access based on user authorization roles
interface RoleGuardProps {
  allowedRoles: ('student' | 'tutor' | 'admin')[];
}

export const RoleGuard = ({ allowedRoles }: RoleGuardProps) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const userRoles = user.roles.map((r) => r.name);
  const hasAccess = allowedRoles.some((role) => userRoles.includes(role));

  if (!hasAccess) {
    // If not authorized, redirect to their default home
    if (userRoles.includes('admin')) return <Navigate to="/admin" replace />;
    if (userRoles.includes('tutor')) return <Navigate to="/tutor" replace />;
    return <Navigate to="/student" replace />;
  }

  return <Outlet />;
};

// Default Landing Redirect logic based on active user role
export const DashboardRedirect: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const userRoles = user.roles.map((r) => r.name);
  if (userRoles.includes('admin')) return <Navigate to="/admin" replace />;
  if (userRoles.includes('tutor')) return <Navigate to="/tutor" replace />;
  return <Navigate to="/student" replace />;
};
