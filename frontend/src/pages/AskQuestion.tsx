import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Enrollment, Question } from '../types';
import { motion } from 'framer-motion';
import { BookOpen, FileText, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';

export const AskQuestion: React.FC = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Enrollment[]>([]);
  const [courseId, setCourseId] = useState('');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);

  useEffect(() => {
    const fetchEnrollments = async () => {
      try {
        const res = await api.get<Enrollment[]>('/students/courses');
        setCourses(res.data);
        if (res.data.length > 0) {
          setCourseId(res.data[0].course_id);
        }
      } catch (err) {
        console.error('Failed to load courses');
      } finally {
        setIsLoadingCourses(false);
      }
    };
    fetchEnrollments();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await api.post<Question>('/questions/', {
        title,
        content,
        course_id: courseId
      });
      navigate(`/questions/${res.data.id}`);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Failed to submit doubt query. Please check your inputs.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingCourses) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-4 page-transit">
      
      {/* Back button link */}
      <button 
        onClick={() => navigate(-1)} 
        className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-700 font-semibold mb-6 transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Dashboard
      </button>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-white rounded-3xl border border-slate-200/60 p-8 shadow-sm flex flex-col gap-6"
      >
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Ask a New Doubt</h2>
          <p className="text-slate-400 text-xs mt-1">Submit your doubt query. The AI system will match similar issues.</p>
        </div>

        {courses.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-700">
            You must be enrolled in at least one course to submit doubts.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-3">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Course Selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-slate-400" />
                Select Course
              </label>
              <select
                value={courseId}
                onChange={(e) => setCourseId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-sm bg-white"
              >
                {courses.map((enr) => (
                  <option key={enr.course_id} value={enr.course_id}>
                    {enr.course?.code} - {enr.course?.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Title Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                Doubt Summary / Title
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Docker container fails to mount local Postgres volume"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-sm"
              />
            </div>

            {/* Content Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-500">Detailed Description</label>
              <textarea
                required
                rows={6}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Describe your doubt here. Include any error logs, trace logs, or steps to reproduce the issue so that your course tutor can assist you."
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-sm resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm shadow-lg shadow-brand-600/15 hover:shadow-brand-600/25 transition-all flex items-center justify-center gap-2 group mt-2"
            >
              {isSubmitting ? 'Routing to AI engine...' : 'Submit Doubt'}
              {!isSubmitting && <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
            </button>
          </form>
        )}
      </motion.div>
    </div>
  );
};
export default AskQuestion;
