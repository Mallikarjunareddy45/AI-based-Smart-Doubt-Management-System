import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  BookOpen, 
  HelpCircle, 
  Layers, 
  TrendingUp, 
  Settings, 
  GraduationCap,
  Shield,
  UserCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();

  const isCurrentAdmin = location.pathname.startsWith('/admin');
  const isCurrentTutor = location.pathname.startsWith('/tutor');

  // Define navigation links based on current active workspace path
  const getNavLinks = () => {
    if (isCurrentAdmin) {
      return [
        { path: '/admin', label: 'Workloads', icon: Layers },
        { path: '/admin/courses', label: 'Courses', icon: BookOpen },
        { path: '/admin/analytics', label: 'System Analytics', icon: TrendingUp },
        { path: '/admin/settings', label: 'AI Settings', icon: Settings },
      ];
    }
    if (isCurrentTutor) {
      return [
        { path: '/tutor', label: 'My Queue', icon: Layers },
        { path: '/tutor/history', label: 'Resolved', icon: BookOpen },
        { path: '/tutor/analytics', label: 'Performance', icon: TrendingUp },
      ];
    }
    // Student links
    return [
      { path: '/student', label: 'My Enrolled', icon: BookOpen },
      { path: '/student/questions', label: 'My Doubts', icon: HelpCircle },
      { path: '/student/ask', label: 'Ask Doubt', icon: GraduationCap },
    ];
  };

  const navLinks = getNavLinks();

  return (
    <aside className="w-64 h-screen border-r border-slate-200/60 bg-white flex flex-col justify-between p-6 shrink-0 sticky top-0">
      <div className="flex flex-col gap-6">
        {/* Brand logo branding */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-800 leading-tight">DoubtAssist</h1>
            <span className="text-[11px] text-brand-600 font-semibold tracking-wider uppercase">Direct Workspace</span>
          </div>
        </div>

        {/* Workspace View Selector */}
        <div className="bg-slate-100/80 p-1.5 rounded-xl flex items-center justify-between text-xs font-semibold text-slate-600">
          <Link
            to="/student"
            className={`flex-1 py-1.5 text-center rounded-lg transition-all ${
              !isCurrentAdmin && !isCurrentTutor
                ? 'bg-white text-brand-600 shadow-sm'
                : 'hover:text-slate-900'
            }`}
          >
            Student
          </Link>
          <Link
            to="/tutor"
            className={`flex-1 py-1.5 text-center rounded-lg transition-all ${
              isCurrentTutor
                ? 'bg-white text-brand-600 shadow-sm'
                : 'hover:text-slate-900'
            }`}
          >
            Tutor
          </Link>
          <Link
            to="/admin"
            className={`flex-1 py-1.5 text-center rounded-lg transition-all ${
              isCurrentAdmin
                ? 'bg-white text-brand-600 shadow-sm'
                : 'hover:text-slate-900'
            }`}
          >
            Admin
          </Link>
        </div>

        {/* Navigation list */}
        <nav className="flex flex-col gap-1.5">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-brand-50 text-brand-600 font-semibold'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-brand-600' : 'text-slate-400'}`} />
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Profile info footer */}
      <div className="flex flex-col gap-4 border-t border-slate-100 pt-6">
        <div className="flex items-center gap-3 px-2">
          <div className="h-9 w-9 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold uppercase border border-brand-200">
            {user ? `${user.first_name[0]}${user.last_name[0]}` : 'GU'}
          </div>
          <div className="overflow-hidden">
            <h4 className="text-xs font-semibold text-slate-800 truncate leading-none mb-1">
              {user ? user.full_name : 'Guest User'}
            </h4>
            <span className="text-[10px] text-emerald-600 font-semibold capitalize truncate block leading-none">
              Direct Access Enabled
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};

