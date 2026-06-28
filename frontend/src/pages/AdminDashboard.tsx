import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useSocket } from '../context/SocketContext';
import { Settings, BarChart2, Layers, CheckSquare, Shield, Sliders, PlayCircle, Plus, Trash2, Edit3, Users } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { registerListener } = useSocket();
  const [stats, setStats] = useState<any>(null);
  const [tutors, setTutors] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [aiSettings, setAiSettings] = useState<any>({ similarity_threshold: 0.82 });
  const [activeClusters, setActiveClusters] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [updatingSettings, setUpdatingSettings] = useState(false);
  const [courseCode, setCourseCode] = useState('');
  const [courseTitle, setCourseTitle] = useState('');
  const [courseDesc, setCourseDesc] = useState('');
  const [creatingCourse, setCreatingCourse] = useState(false);
  const [courseError, setCourseError] = useState<string | null>(null);
  const [courseSuccess, setCourseSuccess] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const [statsRes, tutorsRes, settingsRes, clustersRes, coursesRes, studentsRes] = await Promise.all([
        api.get('/analytics/dashboard'),
        api.get('/admin/tutors'),
        api.get('/admin/settings'),
        api.get('/tutors/clusters/unassigned'),
        api.get('/admin/courses'),
        api.get('/admin/students')
      ]);
      setStats(statsRes.data);
      setTutors(tutorsRes.data);
      setAiSettings(settingsRes.data);
      setCourses(coursesRes.data);
      setStudents(studentsRes.data);
      
      // Fetch all non-resolved clusters for manual override listing
      const allClustersRes = await api.get('/tutors/clusters'); // Mock / fallback list
      setActiveClusters(allClustersRes.data);
    } catch (err) {
      console.error('Failed to load admin dashboard parameters');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Live update stats on socket triggers
    const unsubscribe = registerListener('queue_updated', () => {
      fetchDashboardData();
    });

    return () => {
      unsubscribe();
    };
  }, [registerListener]);

  const handleUpdateThreshold = async (val: number) => {
    try {
      setUpdatingSettings(true);
      await api.put(`/admin/settings?similarity_threshold=${val}`);
      setAiSettings((prev: any) => ({ ...prev, similarity_threshold: val }));
    } catch (err) {
      console.error('Failed to update AI settings');
    } finally {
      setUpdatingSettings(false);
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setCourseError(null);
    setCourseSuccess(null);
    setCreatingCourse(true);
    try {
      await api.post('/admin/courses', {
        code: courseCode,
        title: courseTitle,
        description: courseDesc
      });
      setCourseSuccess(`Course ${courseCode} created successfully!`);
      setCourseCode('');
      setCourseTitle('');
      setCourseDesc('');
    } catch (err: any) {
      setCourseError(err.response?.data?.detail || 'Failed to create course');
    } finally {
      setCreatingCourse(false);
    }
  };

  const handleDeleteCourse = async (courseId: string) => {
    try {
      await api.delete(`/admin/courses/${courseId}`);
      setCourses((prev) => prev.filter((c) => c.id !== courseId));
    } catch (err) {
      console.error('Failed to delete course');
    }
  };

  const handleToggleTutor = async (tutorId: string) => {
    try {
      const res = await api.put(`/admin/tutors/${tutorId}/toggle-availability`);
      setTutors((prev) =>
        prev.map((t) =>
          t.tutor_id === tutorId ? { ...t, is_available: res.data.is_available } : t
        )
      );
    } catch (err) {
      console.error('Failed to toggle tutor availability');
    }
  };

  const handleReassign = async (clusterId: string, tutorId: string) => {
    try {
      await api.post(`/admin/clusters/${clusterId}/assign/${tutorId}`);
      fetchDashboardData();
      alert('Tutor assigned successfully (Manual Override)');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Assignment override failed');
    }
  };

  if (isLoading || !stats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 page-transit">
      
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Unresolved Doubts</span>
          <span className="text-3xl font-extrabold text-slate-800">{stats.questions?.pending}</span>
          <div className="text-[10px] text-slate-400 mt-1">Pending AI clustering</div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Active Clusters</span>
          <span className="text-3xl font-extrabold text-brand-600">{stats.clusters?.active}</span>
          <div className="text-[10px] text-slate-400 mt-1">Claimed or queued</div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Resolved Doubts</span>
          <span className="text-3xl font-extrabold text-emerald-600">{stats.questions?.resolved}</span>
          <div className="text-[10px] text-slate-400 mt-1">Completed by tutors</div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Avg Wait Latency</span>
          <span className="text-3xl font-extrabold text-slate-800">
            {stats.average_resolution_wait_seconds > 0 
              ? `${(stats.average_resolution_wait_seconds / 60).toFixed(1)}m` 
              : 'N/A'}
          </span>
          <div className="text-[10px] text-slate-400 mt-1">Rolling last 7 days</div>
        </div>
      </div>

      {/* Main Sections layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Workload and AI settings */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          
          {/* Tutor Workloads */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-4">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <BarChart2 className="h-4.5 w-4.5 text-slate-500" />
              Tutor Queue Distribution
            </h3>

            <div className="flex flex-col gap-4">
              {tutors.map((tutor) => {
                const percent = Math.min(100, (tutor.active_clusters / tutor.max_workload) * 100);
                return (
                  <div key={tutor.tutor_id} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                      <div className="flex items-center gap-2">
                        <span>{tutor.full_name} ({tutor.department || 'CS'})</span>
                        <button
                          onClick={() => handleToggleTutor(tutor.tutor_id)}
                          className={`px-1.5 py-0.5 rounded text-[8px] font-bold border transition-colors ${
                            tutor.is_available 
                              ? 'bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-100' 
                              : 'bg-rose-50 text-rose-600 border-rose-100 hover:bg-emerald-50 hover:text-emerald-600 hover:border-emerald-100'
                          }`}
                          title={tutor.is_available ? "Set Offline" : "Set Online"}
                        >
                          {tutor.is_available ? 'ONLINE' : 'OFFLINE'}
                        </button>
                      </div>
                      <span>{tutor.active_clusters} / {tutor.max_workload} Active</span>
                    </div>
                    {/* Visual Progress bar */}
                    <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          percent >= 80 ? 'bg-rose-500' : percent >= 50 ? 'bg-amber-500' : 'bg-brand-500'
                        }`} 
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Manual Assignment Override list */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-4">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Shield className="h-4.5 w-4.5 text-slate-500" />
              AI Assignment Override Controls
            </h3>

            {activeClusters.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No active question clusters to override.
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {activeClusters.map((cluster) => (
                  <div 
                    key={cluster.id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200/50 flex items-center justify-between gap-4 text-xs"
                  >
                    <div className="overflow-hidden">
                      <h4 className="font-semibold text-slate-800 truncate">{cluster.summary || 'Doubt Cluster'}</h4>
                      <span className="text-[10px] text-slate-400">Score: {cluster.priority_score.toFixed(1)}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <label className="text-[10px] font-bold text-slate-400 uppercase">Reassign To</label>
                      <select
                        onChange={(e) => handleReassign(cluster.id, e.target.value)}
                        value={cluster.assigned_tutor_id || ''}
                        className="p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                      >
                        <option value="">-- Select Tutor --</option>
                        {tutors.map((t) => (
                          <option key={t.tutor_id} value={t.tutor_id}>
                            {t.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Course Catalog List */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-4">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Layers className="h-4.5 w-4.5 text-slate-500" />
              Active Course Catalogue ({courses.length})
            </h3>
            
            {courses.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs bg-slate-50 rounded-xl">
                No active courses in catalog. Create one using the side panel.
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {courses.map((course) => (
                  <div 
                    key={course.id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200/50 flex items-center justify-between gap-4 text-xs animate-fade-in"
                  >
                    <div className="overflow-hidden">
                      <h4 className="font-semibold text-slate-800 truncate">
                        <span className="text-[10px] text-brand-600 font-bold bg-brand-50 border border-brand-100 px-1.5 py-0.5 rounded mr-1.5">
                          {course.code}
                        </span>
                        {course.title}
                      </h4>
                      <p className="text-[10px] text-slate-400 truncate mt-1">{course.description || 'No description provided.'}</p>
                    </div>
                    
                    <button
                      onClick={() => handleDeleteCourse(course.id)}
                      className="p-2 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors shrink-0"
                      title="Delete Course"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Registered Students Directory */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-4">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Users className="h-4.5 w-4.5 text-slate-500" />
              Registered Student Roster ({students.length})
            </h3>
            
            {students.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs bg-slate-50 rounded-xl">
                No students registered in the system yet.
              </div>
            ) : (
              <div className="flex flex-col gap-3 max-h-80 overflow-y-auto pr-1">
                {students.map((st) => (
                  <div 
                    key={st.student_id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200/50 flex items-center justify-between gap-4 text-xs"
                  >
                    <div className="overflow-hidden flex-1">
                      <h4 className="font-semibold text-slate-800 truncate">{st.full_name}</h4>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">{st.email}</p>
                      <p className="text-[9px] text-slate-400 mt-1">
                        Matriculation: <span className="font-bold text-slate-600">{st.matriculation_number || 'N/A'}</span>
                      </p>
                    </div>
                    
                    <span className="px-2 py-1 bg-slate-100 border border-slate-200 rounded-lg text-[10px] font-bold text-slate-500 shrink-0">
                      {st.enrollments_count} Courses
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: AI Dial Settings */}
        <div className="flex flex-col gap-4">
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-5">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Sliders className="h-4.5 w-4.5 text-slate-500" />
              AI Calibration Console
            </h3>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                <label>Semantic Match Threshold</label>
                <span className="text-brand-600">{aiSettings.similarity_threshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="0.99"
                step="0.01"
                value={aiSettings.similarity_threshold}
                disabled={updatingSettings}
                onChange={(e) => handleUpdateThreshold(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <p className="text-[10px] text-slate-400 leading-relaxed mt-1">
                Higher settings require questions to be near-identical to merge. Lower settings group wider topic variations. Recommended: 0.80 - 0.85.
              </p>
            </div>
          </div>

          {/* Create Course Panel */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/60 flex flex-col gap-4">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Plus className="h-4.5 w-4.5 text-slate-500" />
              Create New Course
            </h3>
            
            <form onSubmit={handleCreateCourse} className="flex flex-col gap-3.5">
              {courseError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-700 text-[10px]">
                  {courseError}
                </div>
              )}
              {courseSuccess && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-[10px]">
                  {courseSuccess}
                </div>
              )}
              
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Course Code</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. CS-101"
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  className="px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Course Title</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. Intro to Computer Science"
                  value={courseTitle}
                  onChange={(e) => setCourseTitle(e.target.value)}
                  className="px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Description</label>
                <textarea 
                  placeholder="e.g. Basic concepts of algorithms..."
                  value={courseDesc}
                  onChange={(e) => setCourseDesc(e.target.value)}
                  rows={3}
                  className="px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-brand-500 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={creatingCourse}
                className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5"
              >
                {creatingCourse ? 'Creating...' : 'Create Course'}
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
};
export default AdminDashboard;
