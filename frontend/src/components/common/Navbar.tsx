import React, { useState, useEffect } from 'react';
import { useSocket } from '../../context/SocketContext';
import { Bell, Wifi, WifiOff, CheckCircle } from 'lucide-react';
import api from '../../services/api';
import { Notification } from '../../types';

export const Navbar: React.FC = () => {
  const { isConnected, registerListener } = useSocket();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState<boolean>(false);

  // Fetch notifications on mount
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await api.get<Notification[]>('/analytics/notifications');
        setNotifications(res.data);
      } catch (err) {
        console.error('Failed to load notifications');
      }
    };
    fetchNotifications();

    // Register socket listener to receive real-time notifications
    const unsubscribe = registerListener('cluster_assigned', (data) => {
      const newNotif: Notification = {
        id: Math.random().toString(),
        recipient_id: '',
        title: 'New assignment',
        content: data.summary || 'A new question cluster was assigned to you.',
        type: 'cluster_assigned',
        is_read: false,
        created_at: new Date().toISOString()
      };
      setNotifications(prev => [newNotif, ...prev]);
    });

    const unsubscribe2 = registerListener('question_analyzed', (data) => {
      const newNotif: Notification = {
        id: Math.random().toString(),
        recipient_id: '',
        title: 'Doubt status updated',
        content: `Your doubt has been mapped to cluster ${data.cluster_id}`,
        type: 'doubt_processed',
        is_read: false,
        created_at: new Date().toISOString()
      };
      setNotifications(prev => [newNotif, ...prev]);
    });

    return () => {
      unsubscribe();
      unsubscribe2();
    };
  }, [registerListener]);

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    setShowNotifications(false);
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="h-16 border-b border-slate-200/60 bg-white/70 backdrop-blur-md sticky top-0 z-40 flex items-center justify-between px-8">
      {/* Title info */}
      <div>
        <h2 className="text-slate-800 font-semibold text-lg">Doubt Workspace</h2>
      </div>

      {/* Action items */}
      <div className="flex items-center gap-4">
        {/* Real-time WebSockets status badge */}
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
          isConnected 
            ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/50' 
            : 'bg-amber-50 text-amber-600 border border-amber-200/50'
        }`}>
          {isConnected ? (
            <>
              <Wifi className="h-3.5 w-3.5 animate-pulse" />
              <span>Live Synced</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5" />
              <span>Offline Cache</span>
            </>
          )}
        </div>

        {/* Notification Bell with relative dropdown panel */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="h-10 w-10 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors relative border border-slate-200/40"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-4 w-4 rounded-full bg-rose-500 text-white flex items-center justify-center text-[9px] font-bold ring-2 ring-white">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden z-50">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800 text-sm">Notifications</h3>
                {unreadCount > 0 && (
                  <button 
                    onClick={markAllRead}
                    className="text-xs text-brand-600 hover:text-brand-800 font-medium"
                  >
                    Mark read
                  </button>
                )}
              </div>
              <div className="max-h-60 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No active notifications
                  </div>
                ) : (
                  notifications.map(notif => (
                    <div 
                      key={notif.id} 
                      className={`p-4 border-b border-slate-50 flex flex-col gap-1 transition-colors ${
                        notif.is_read ? 'bg-white' : 'bg-slate-50/50'
                      }`}
                    >
                      <h4 className="text-xs font-semibold text-slate-800">{notif.title}</h4>
                      <p className="text-[11px] text-slate-500 leading-relaxed">{notif.content}</p>
                      <span className="text-[9px] text-slate-400 mt-1">Just now</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
