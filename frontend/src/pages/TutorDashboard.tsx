import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { QuestionCluster } from '../types';
import { Layers, CheckCircle, Clock, Users, ArrowRight, UserPlus, Play, BookOpen } from 'lucide-react';
import { useSocket } from '../context/SocketContext';

export const TutorDashboard: React.FC = () => {
  const { registerListener } = useSocket();
  const [myClusters, setMyClusters] = useState<QuestionCluster[]>([]);
  const [unassignedClusters, setUnassignedClusters] = useState<QuestionCluster[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchQueues = async () => {
    try {
      setIsLoading(true);
      const [myRes, unassignedRes, coursesRes] = await Promise.all([
        api.get<QuestionCluster[]>('/tutors/clusters'),
        api.get<QuestionCluster[]>('/tutors/clusters/unassigned'),
        api.get<any[]>('/courses')
      ]);
      setMyClusters(myRes.data);
      setUnassignedClusters(unassignedRes.data);
      setCourses(coursesRes.data);
    } catch (err) {
      console.error('Failed to load tutor queues');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueues();

    // Reload queues in real-time if updates are signaled over WS
    const unsubscribe = registerListener('queue_updated', () => {
      fetchQueues();
    });

    const unsubscribe2 = registerListener('tutor_claimed', () => {
      fetchQueues();
    });

    return () => {
      unsubscribe();
      unsubscribe2();
    };
  }, [registerListener]);

  const handleClaim = async (clusterId: string) => {
    try {
      await api.post(`/tutors/clusters/${clusterId}/claim`);
      fetchQueues();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to claim cluster');
    }
  };

  const handleResolve = async (clusterId: string) => {
    try {
      await api.post(`/tutors/clusters/${clusterId}/resolve`);
      fetchQueues();
    } catch (err) {
      console.error('Failed to resolve cluster');
    }
  };

  // Priority color categorizer utility
  const getPriorityBadge = (score: number) => {
    if (score >= 4.0) return 'bg-rose-50 text-rose-700 border-rose-200';
    if (score >= 2.0) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-slate-50 text-slate-600 border-slate-200';
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
      
      {/* Triage Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Column 1: Unassigned Clusters Queue */}
        <div className="flex flex-col gap-4">
          <h3 className="text-slate-800 font-bold text-base flex items-center gap-2">
            <Users className="h-4.5 w-4.5 text-slate-500" />
            Unassigned Doubt Clusters ({unassignedClusters.length})
          </h3>
          
          {unassignedClusters.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-sm">
              All question clusters are currently claimed.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {unassignedClusters.map((cluster) => (
                <div 
                  key={cluster.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-4 hover-premium"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="overflow-hidden">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${getPriorityBadge(cluster.priority_score)}`}>
                        Priority: {cluster.priority_score.toFixed(1)}
                      </span>
                      <h4 className="font-semibold text-slate-800 text-sm truncate mt-2">
                        {cluster.summary || 'AI Doubt Cluster'}
                      </h4>
                    </div>
                    <button
                      onClick={() => handleClaim(cluster.id)}
                      className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1 transition-colors shrink-0 shadow-sm"
                    >
                      <UserPlus className="h-3.5 w-3.5" />
                      Claim
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-3 mt-1">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      Created {new Date(cluster.created_at).toLocaleTimeString()}
                    </span>
                    <Link 
                      to={`/tutor/clusters/${cluster.id}`} 
                      className="text-brand-600 hover:underline font-semibold flex items-center gap-0.5"
                    >
                      View Details
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Column 2: My Assigned Clusters */}
        <div className="flex flex-col gap-4">
          <h3 className="text-slate-800 font-bold text-base flex items-center gap-2">
            <Layers className="h-4.5 w-4.5 text-slate-500" />
            My Active Clusters ({myClusters.length})
          </h3>
          
          {myClusters.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-sm">
              You do not have any active clusters assigned.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {myClusters.map((cluster) => (
                <div 
                  key={cluster.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col gap-4 hover-premium"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="overflow-hidden">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${getPriorityBadge(cluster.priority_score)}`}>
                        Priority: {cluster.priority_score.toFixed(1)}
                      </span>
                      <h4 className="font-semibold text-slate-800 text-sm truncate mt-2">
                        {cluster.summary || 'AI Doubt Cluster'}
                      </h4>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleResolve(cluster.id)}
                        className="p-1.5 rounded-lg border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 transition-colors"
                        title="Mark Resolved"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                      <Link
                        to={`/tutor/clusters/${cluster.id}`}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-1 transition-colors shadow-sm"
                      >
                        <Play className="h-3 w-3 fill-current" />
                        Reply
                      </Link>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-3 mt-1">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      Assigned {new Date(cluster.updated_at).toLocaleTimeString()}
                    </span>
                    <Link 
                      to={`/tutor/clusters/${cluster.id}`} 
                      className="text-brand-600 hover:underline font-semibold flex items-center gap-0.5"
                    >
                      View Thread
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Tutor Courses List */}
      <div className="flex flex-col gap-4 mt-8 border-t border-slate-100 pt-8">
        <h3 className="text-slate-800 font-bold text-base flex items-center gap-2">
          <BookOpen className="h-4.5 w-4.5 text-slate-500" />
          My Courses (Syllabus Builder)
        </h3>
        
        {courses.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-sm">
            No courses found.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {courses.map((course) => (
              <div key={course.id} className="p-5 rounded-2xl bg-white border border-slate-200/60 flex flex-col justify-between gap-3 shadow-sm hover-premium">
                <div>
                  <span className="text-[10px] text-brand-600 font-semibold tracking-wide uppercase">{course.code}</span>
                  <h4 className="font-semibold text-slate-800 text-sm truncate">{course.title}</h4>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{course.description || 'No description'}</p>
                </div>
                <Link 
                  to={`/tutor/courses/${course.id}/edit`} 
                  className="w-full text-center px-4 py-2 rounded-lg bg-indigo-50 border border-indigo-200/40 text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all text-xs font-semibold"
                >
                  Edit Course Syllabus
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
export default TutorDashboard;
