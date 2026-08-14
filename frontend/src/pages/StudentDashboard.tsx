import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Enrollment, Question } from '../types';
import { BookOpen, HelpCircle, CheckCircle, Clock, ChevronRight, Plus, ThumbsUp } from 'lucide-react';
import { useSocket } from '../context/SocketContext';

export const StudentDashboard: React.FC = () => {
  const { registerListener } = useSocket();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [coursesRes, doubtsRes, notifsRes] = await Promise.all([
        api.get<Enrollment[]>('/students/courses'),
        api.get<Question[]>('/students/questions'),
        api.get<any[]>('/analytics/notifications')
      ]);
      setEnrollments(coursesRes.data);
      setQuestions(doubtsRes.data);
      setNotifications(notifsRes.data);
    } catch (err) {
      console.error('Failed to load student dashboard metrics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Register live websocket listener to update question state dynamically
    const unsubscribe = registerListener('question_analyzed', (data) => {
      setQuestions((prev) => 
        prev.map((q) => 
          q.id === data.question_id 
            ? { ...q, cluster_id: data.cluster_id, status: data.status } 
            : q
        )
      );
    });

    return () => {
      unsubscribe();
    };
  }, [registerListener]);

  const handleUpvote = async (questionId: string) => {
    try {
      const res = await api.post<Question>(`/questions/${questionId}/upvote`);
      setQuestions((prev) => prev.map((q) => (q.id === questionId ? res.data : q)));
    } catch (err) {
      console.error('Failed to upvote doubt');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 page-transit">
      {/* Welcome Banner */}
      <div className="p-8 rounded-3xl bg-gradient-to-r from-brand-600 to-indigo-600 text-white relative overflow-hidden shadow-lg shadow-brand-500/10">
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-xl" />
        <div className="relative z-10 flex flex-col gap-2">
          <h2 className="text-2xl font-bold font-sans">Course Assistance Hub</h2>
          <p className="text-brand-100 text-sm max-w-md">
            Ask doubts in enrolled courses. Our AI engine groups similar questions and matches them with available tutors.
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Enrolled Courses</span>
          <span className="text-xl font-bold text-slate-800">{enrollments.length}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Doubts</span>
          <span className="text-xl font-bold text-slate-800">{questions.length}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pending Doubts</span>
          <span className="text-xl font-bold text-amber-600">{questions.filter(q => q.status !== 'resolved').length}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Resolved Doubts</span>
          <span className="text-xl font-bold text-emerald-600">{questions.filter(q => q.status === 'resolved').length}</span>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Questions lists */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-slate-800 font-bold text-base flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-slate-500" />
              My Doubt Queries
            </h3>
            <Link 
              to="/student/ask" 
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-semibold hover:bg-brand-500 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Ask Doubt
            </Link>
          </div>

          {questions.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-sm">
              You haven't submitted any doubts yet.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {questions.map((q) => (
                <div 
                  key={q.id} 
                  className="p-5 rounded-2xl bg-white border border-slate-200/60 hover-premium flex items-center justify-between gap-4"
                >
                  <div className="flex flex-col gap-1.5 overflow-hidden">
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Status Badges */}
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                        q.status === 'resolved' 
                          ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/40' 
                          : q.status === 'clustered'
                          ? 'bg-indigo-50 text-indigo-600 border border-indigo-200/40'
                          : 'bg-amber-50 text-amber-600 border border-amber-200/40'
                      }`}>
                        {q.status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        Posted {new Date(q.created_at).toLocaleDateString()}
                      </span>
                      {q.assigned_tutor_name && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                          Tutor: {q.assigned_tutor_name}
                        </span>
                      )}
                    </div>

                    <Link to={`/questions/${q.id}`} className="font-semibold text-slate-800 hover:text-brand-600 transition-colors truncate">
                      {q.title}
                    </Link>
                    <p className="text-xs text-slate-400 line-clamp-1">{q.content}</p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      onClick={() => handleUpvote(q.id)}
                      className="h-8 px-3 rounded-lg border border-slate-200 hover:border-brand-500 hover:text-brand-500 flex items-center gap-1.5 text-xs text-slate-400 transition-all active:scale-95"
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                      {q.upvotes_count}
                    </button>
                    <Link to={`/questions/${q.id}`} className="p-2 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-700 transition-colors">
                      <ChevronRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Side: Courses & Workspaces */}
        <div className="flex flex-col gap-4">
          <h3 className="text-slate-800 font-bold text-base flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-slate-500" />
            My Active Courses
          </h3>

          {enrollments.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-xs">
              No registered courses found.{' '}
              <Link to="/student/courses/enroll" className="text-brand-600 font-semibold hover:underline">
                Register now
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {enrollments.map((enr) => (
                <div 
                  key={enr.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-3"
                >
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-center text-slate-600 font-bold text-xs uppercase shrink-0">
                      {enr.course?.code.slice(0, 3)}
                    </div>
                    <div className="overflow-hidden flex-1">
                      <span className="text-[10px] text-brand-600 font-semibold tracking-wide uppercase">
                        {enr.course?.code}
                      </span>
                      <h4 className="font-semibold text-slate-800 text-sm truncate leading-snug">
                        {enr.course?.title}
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                        {enr.course?.description || 'No description provided.'}
                      </p>
                    </div>
                  </div>
                  <Link 
                    to={`/student/courses/${enr.course_id}`} 
                    className="w-full text-center px-4 py-2 rounded-lg bg-indigo-50 border border-indigo-200/40 text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all text-xs font-semibold"
                  >
                    Enter Learning Workspace
                  </Link>
                </div>
              ))}
            </div>
          )}

          {/* Recent Notifications Card */}
          <div className="flex flex-col gap-4 bg-white border border-slate-200/60 p-5 rounded-2xl">
            <h3 className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-500" />
              Recent Notifications
            </h3>
            
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-slate-400 text-xs">
                No recent notifications.
              </div>
            ) : (
              <div className="flex flex-col gap-3 max-h-64 overflow-y-auto pr-1">
                {notifications.slice(0, 5).map((n) => (
                  <div key={n.id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex flex-col gap-1 text-[11px]">
                    <span className="font-semibold text-slate-700">{n.title}</span>
                    <p className="text-slate-500">{n.content}</p>
                    <span className="text-[9px] text-slate-400 mt-0.5">{new Date(n.created_at).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
export default StudentDashboard;
