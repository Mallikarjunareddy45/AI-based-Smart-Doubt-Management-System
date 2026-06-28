import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  BookOpen, 
  HelpCircle, 
  Layers, 
  TrendingUp, 
  Settings, 
  User as UserIcon,
  LogOut,
  GraduationCap
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();

  if (!user) return null;
  const userRoles = user.roles.map((r) => r.name);

  // Define navigation links based on user roles
  const getNavLinks = () => {
    if (userRoles.includes('admin')) {
      return [
        { path: '/admin', label: 'Workloads', icon: Layers },
        { path: '/admin/courses', label: 'Courses', icon: BookOpen },
        { path: '/admin/analytics', label: 'System Analytics', icon: TrendingUp },
        { path: '/admin/settings', label: 'AI Settings', icon: Settings },
      ];
    }
    if (userRoles.includes('tutor')) {
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
      <div className="flex flex-col gap-8">
        {/* Brand logo branding */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-800 leading-tight">DoubtAssist</h1>
            <span className="text-[11px] text-brand-600 font-semibold tracking-wider uppercase">AI Routing System</span>
          </div>
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

      {/* User profile actions summary */}
      <div className="flex flex-col gap-4 border-t border-slate-100 pt-6">
        <div className="flex items-center gap-3 px-2">
          <div className="h-9 w-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-700 font-semibold uppercase border border-slate-200">
            {user.first_name[0]}{user.last_name[0]}
          </div>
          <div className="overflow-hidden">
            <h4 className="text-xs font-semibold text-slate-800 truncate leading-none mb-1">{user.full_name}</h4>
            <span className="text-[10px] text-slate-400 font-medium capitalize truncate block leading-none">
              {userRoles.join(', ')}
            </span>
          </div>
        </div>
        
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-colors w-full"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
};
