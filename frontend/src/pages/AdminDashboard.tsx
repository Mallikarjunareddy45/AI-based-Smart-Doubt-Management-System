import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useSocket } from '../context/SocketContext';
import { 
  Settings, BarChart2, Layers, Shield, Sliders, Plus, 
  Trash2, Users, DollarSign, CreditCard, Sparkles, RefreshCw, 
  BookOpen, CheckCircle2, XCircle, AlertTriangle, UserCheck, UserX 
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { registerListener } = useSocket();
  const [activeTab, setActiveTab] = useState<'analytics' | 'users' | 'categories' | 'financials' | 'settings'>('analytics');
  
  const [stats, setStats] = useState<any>(null);
  const [financials, setFinancials] = useState<any>(null);
  const [aiAnalytics, setAiAnalytics] = useState<any>(null);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [tutors, setTutors] = useState<any[]>([]);
  const [aiSettings, setAiSettings] = useState<any>({ similarity_threshold: 0.82 });
  const [courses, setCourses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Category creation form state
  const [catName, setCatName] = useState('');
  const [catDesc, setCatDesc] = useState('');

  // Course creation form state
  const [courseCode, setCourseCode] = useState('');
  const [courseTitle, setCourseTitle] = useState('');
  const [courseDesc, setCourseDesc] = useState('');

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const [statsRes, tutorsRes, settingsRes, coursesRes, finRes, usersRes, catRes, aiAnaRes] = await Promise.all([
        api.get('/analytics/dashboard').catch(() => ({ data: {} })),
        api.get('/admin/tutors').catch(() => ({ data: [] })),
        api.get('/admin/settings').catch(() => ({ data: { similarity_threshold: 0.82 } })),
        api.get('/admin/courses').catch(() => ({ data: [] })),
        api.get('/admin/financials').catch(() => ({ data: null })),
        api.get('/admin/users').catch(() => ({ data: [] })),
        api.get('/admin/categories').catch(() => ({ data: [] })),
        api.get('/admin/ai-analytics').catch(() => ({ data: null }))
      ]);

      setStats(statsRes.data);
      setTutors(tutorsRes.data);
      setAiSettings(settingsRes.data);
      setCourses(coursesRes.data);
      setFinancials(finRes.data);
      setAllUsers(usersRes.data);
      setCategories(catRes.data);
      setAiAnalytics(aiAnaRes.data);
    } catch (err) {
      console.error('Failed to load Super Admin parameters', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    const unsubscribe = registerListener('queue_updated', () => {
      fetchDashboardData();
    });

    return () => unsubscribe();
  }, [registerListener]);

  const handleUpdateThreshold = async (val: number) => {
    try {
      await api.put(`/admin/settings?similarity_threshold=${val}`);
      setAiSettings((prev: any) => ({ ...prev, similarity_threshold: val }));
    } catch (err) {
      alert('Failed to update AI settings');
    }
  };

  const handleToggleUserStatus = async (userId: string) => {
    try {
      const res = await api.put(`/admin/users/${userId}/status`);
      setAllUsers(prev => prev.map(u => u.user_id === userId ? { ...u, is_active: res.data.is_active } : u));
    } catch (err) {
      alert('Failed to toggle user status');
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!catName.trim()) return;

    try {
      const res = await api.post(`/admin/categories?name=${encodeURIComponent(catName)}&description=${encodeURIComponent(catDesc)}`);
      setCategories(prev => [...prev, res.data]);
      setCatName('');
      setCatDesc('');
    } catch (err) {
      alert('Failed to create category');
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/admin/courses', {
        code: courseCode,
        title: courseTitle,
        description: courseDesc
      });
      setCourses(prev => [...prev, res.data]);
      setCourseCode('');
      setCourseTitle('');
      setCourseDesc('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create course');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 page-transit">
      {/* Super Admin Title */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-indigo-600" />
            Super Admin Console
          </h1>
          <p className="text-xs text-slate-500">Platform Financial Ledger, User Governance & RAG Analytics</p>
        </div>
        <button
          onClick={fetchDashboardData}
          className="p-2 text-slate-500 hover:text-indigo-600 bg-white border border-slate-200 rounded-xl transition-colors shadow-sm flex items-center gap-1 text-xs font-semibold"
        >
          <RefreshCw className="w-4 h-4" /> Refresh Data
        </button>
      </div>

      {/* Tabs Bar */}
      <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200/80 gap-1">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'analytics'
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <BarChart2 className="w-4 h-4" /> System Analytics
        </button>
        <button
          onClick={() => setActiveTab('financials')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'financials'
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <DollarSign className="w-4 h-4" /> Financial Ledger
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'users'
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4" /> User Management ({allUsers.length})
        </button>
        <button
          onClick={() => setActiveTab('categories')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'categories'
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" /> Courses & Categories
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'settings'
              ? 'bg-white text-indigo-600 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Settings className="w-4 h-4" /> AI & Platform Config
        </button>
      </div>

      {/* TAB 1: SYSTEM & RAG ANALYTICS */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {/* KPI Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Total Revenue</span>
              <span className="text-3xl font-black text-emerald-600">${financials?.total_revenue || 0}</span>
              <span className="text-[11px] text-slate-400">USD Course Enrollments</span>
            </div>
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">RAG Vector Embeddings</span>
              <span className="text-3xl font-black text-indigo-600">{aiAnalytics?.total_vector_embeddings || 0}</span>
              <span className="text-[11px] text-slate-400">Indexed Course Chunks</span>
            </div>
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">AI Chat Queries</span>
              <span className="text-3xl font-black text-brand-600">{aiAnalytics?.total_ai_chat_queries || 0}</span>
              <span className="text-[11px] text-slate-400">Student AI Tutor Calls</span>
            </div>
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Registered Users</span>
              <span className="text-3xl font-black text-slate-800">{allUsers.length}</span>
              <span className="text-[11px] text-slate-400">Students, Instructors & Admins</span>
            </div>
          </div>

          {/* AI Metrics Panel */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold">RAG Vector Knowledge Base & AI Tutor Health</h3>
              </div>
              <span className="text-xs px-2.5 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-full font-mono font-medium">
                {aiAnalytics?.embedding_model || 'SentenceTransformers'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[11px]">Average Grounded RAG Confidence</span>
                <span className="text-xl font-bold text-emerald-400">
                  {Math.round((aiAnalytics?.average_rag_confidence || 0.85) * 100)}%
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[11px]">Doubt Escalations to Tutors</span>
                <span className="text-xl font-bold text-amber-400">
                  {aiAnalytics?.escalated_doubt_queries || 0}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[11px]">Vector Feature Dimension</span>
                <span className="text-xl font-bold text-indigo-400">
                  {aiAnalytics?.vector_dimensions || 384}-d Dense Vector
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: FINANCIAL LEDGER */}
      {activeTab === 'financials' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-indigo-600" /> Platform Transaction History Ledger
              </h3>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                Total Revenue: ${financials?.total_revenue || 0} USD
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Transaction ID</th>
                    <th className="p-3">Amount</th>
                    <th className="p-3">Payment Method</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {financials?.recent_transactions && financials.recent_transactions.length > 0 ? (
                    financials.recent_transactions.map((tx: any) => (
                      <tr key={tx.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="p-3 font-semibold text-slate-800">{tx.transaction_id}</td>
                        <td className="p-3 font-bold text-emerald-600">${tx.amount.toFixed(2)} {tx.currency}</td>
                        <td className="p-3 uppercase text-slate-500">{tx.payment_method}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            tx.status === 'succeeded' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                          }`}>
                            {tx.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400">{new Date(tx.created_at).toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-slate-400 font-sans">
                        No financial checkout transactions recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: USER MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-600" /> Platform User & Governance Directory ({allUsers.length})
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Full Name</th>
                    <th className="p-3">Email Address</th>
                    <th className="p-3">System Roles</th>
                    <th className="p-3">Account Status</th>
                    <th className="p-3 text-right">Governance Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {allUsers.map(u => (
                    <tr key={u.user_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3 font-semibold text-slate-800">{u.full_name}</td>
                      <td className="p-3 font-mono text-slate-600">{u.email}</td>
                      <td className="p-3">
                        {u.roles.map((r: string, rIdx: number) => (
                          <span key={rIdx} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 font-bold uppercase rounded text-[10px] mr-1">
                            {r}
                          </span>
                        ))}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                          {u.is_active ? 'Active Account' : 'Suspended'}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => handleToggleUserStatus(u.user_id)}
                          className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-colors ${
                            u.is_active 
                              ? 'bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100'
                              : 'bg-emerald-50 border-emerald-200 text-emerald-600 hover:bg-emerald-100'
                          }`}
                        >
                          {u.is_active ? 'Suspend User' : 'Activate User'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: CATEGORIES & COURSES */}
      {activeTab === 'categories' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Category Manager */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" /> Category Management ({categories.length})
            </h3>

            <form onSubmit={handleCreateCategory} className="space-y-3 pt-2">
              <input
                type="text"
                value={catName}
                onChange={e => setCatName(e.target.value)}
                placeholder="Category Name (e.g. Artificial Intelligence)"
                className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs focus:border-indigo-500 focus:outline-none"
              />
              <input
                type="text"
                value={catDesc}
                onChange={e => setCatDesc(e.target.value)}
                placeholder="Category Description"
                className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1"
              >
                <Plus className="w-4 h-4" /> Add Category
              </button>
            </form>

            <div className="space-y-2 pt-2">
              {categories.map(c => (
                <div key={c.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex justify-between items-center text-xs">
                  <div>
                    <span className="font-bold text-slate-800 block">{c.name}</span>
                    <span className="text-slate-400 text-[11px]">{c.description || 'No description'}</span>
                  </div>
                  <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded font-semibold text-[10px]">
                    {c.courses_count} Courses
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Course Builder Launcher */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" /> Platform Courses Directory ({courses.length})
            </h3>

            <form onSubmit={handleCreateCourse} className="space-y-3 pt-2">
              <input
                type="text"
                value={courseCode}
                onChange={e => setCourseCode(e.target.value)}
                placeholder="Course Code (e.g. CS101)"
                className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs focus:border-indigo-500 focus:outline-none"
              />
              <input
                type="text"
                value={courseTitle}
                onChange={e => setCourseTitle(e.target.value)}
                placeholder="Course Title"
                className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs focus:border-indigo-500 focus:outline-none"
              />
              <textarea
                value={courseDesc}
                onChange={e => setCourseDesc(e.target.value)}
                placeholder="Course Description"
                rows={2}
                className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1"
              >
                <Plus className="w-4 h-4" /> Create Course
              </button>
            </form>

            <div className="space-y-2 pt-2">
              {courses.map(crs => (
                <div key={crs.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex justify-between items-center text-xs">
                  <div>
                    <span className="font-mono text-indigo-600 font-bold block">{crs.code}</span>
                    <span className="font-semibold text-slate-800">{crs.title}</span>
                  </div>
                  <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 font-bold rounded text-[10px]">
                    ${crs.price}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: AI & PLATFORM SETTINGS */}
      {activeTab === 'settings' && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-6">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-600" /> RAG Similarity Threshold & System Parameters
          </h3>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3 max-w-xl">
            <div className="flex justify-between text-xs font-semibold text-slate-700">
              <span>Vector Cosine Similarity Threshold</span>
              <span className="font-mono text-indigo-600 font-bold">{aiSettings.similarity_threshold}</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.01"
              value={aiSettings.similarity_threshold}
              onChange={e => setAiSettings({ ...aiSettings, similarity_threshold: parseFloat(e.target.value) })}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <button
              onClick={() => handleUpdateThreshold(aiSettings.similarity_threshold)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-sm transition-colors"
            >
              Save AI Threshold
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
