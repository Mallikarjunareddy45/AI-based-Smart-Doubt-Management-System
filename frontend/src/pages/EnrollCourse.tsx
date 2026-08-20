import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { Course, Enrollment } from '../types';
import { Search, BookOpen, CheckCircle, ArrowLeft, Loader2, Sparkles, CreditCard } from 'lucide-react';
import { motion } from 'framer-motion';
import { CheckoutModal } from '../components/payment/CheckoutModal';

export const EnrollCourse: React.FC = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrolledIds, setEnrolledIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [enrollingId, setEnrollingId] = useState<string | null>(null);

  // Checkout Modal State
  const [selectedCourseForCheckout, setSelectedCourseForCheckout] = useState<any | null>(null);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);

  const fetchCourses = async () => {
    try {
      setIsLoading(true);
      const [availableRes, activeRes] = await Promise.all([
        api.get<Course[]>('/students/courses/available'),
        api.get<Enrollment[]>('/students/courses')
      ]);
      setCourses(availableRes.data);
      setEnrolledIds(activeRes.data.map((enr) => enr.course_id));
    } catch (err) {
      console.error('Failed to load courses catalogue');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleEnrollClick = (course: any) => {
    setSelectedCourseForCheckout(course);
    setIsCheckoutOpen(true);
  };

  // Filter based on search queries
  const filteredCourses = courses.filter((c) => 
    c.code.toLowerCase().includes(searchQuery.toLowerCase()) || 
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 page-transit">
      {/* Header bar actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link 
            to="/student"
            className="p-2 rounded-xl bg-white border border-slate-200/60 text-slate-500 hover:text-slate-700 hover:shadow-sm transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-slate-800 font-sans flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-brand-500" />
              Course Catalog
            </h2>
            <p className="text-xs text-slate-400">Search and register for course doubt rooms</p>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input 
            type="text"
            placeholder="Search by code or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200/60 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20 transition-all placeholder:text-slate-400"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200/60 text-slate-400 text-sm">
          No courses matching your search criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((c) => {
            const isEnrolled = enrolledIds.includes(c.id);
            const isEnrolling = enrollingId === c.id;

            return (
              <motion.div 
                key={c.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl border border-slate-200/60 p-6 flex flex-col justify-between gap-5 hover-premium relative overflow-hidden"
              >
                {isEnrolled && (
                  <div className="absolute right-0 top-0 h-16 w-16 overflow-hidden pointer-events-none">
                    <div className="absolute top-2.5 right-[-24px] rotate-45 bg-emerald-500 text-white text-[9px] font-bold py-0.5 px-6 uppercase tracking-wider text-center shadow-sm">
                      Enrolled
                    </div>
                  </div>
                )}
                
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] text-brand-600 font-bold uppercase tracking-wider bg-brand-50/70 border border-brand-100/50 px-2 py-0.5 rounded-md self-start">
                    {c.code}
                  </span>
                  <h3 className="font-bold text-slate-800 text-base leading-snug">
                    {c.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                    {c.description || 'No description available for this course module.'}
                  </p>
                </div>

                <button
                  disabled={isEnrolled || isEnrolling}
                  onClick={() => handleEnrollClick(c)}
                  className={`w-full py-2.5 rounded-xl font-semibold text-xs transition-all flex items-center justify-center gap-1.5 ${
                    isEnrolled 
                      ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' 
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20 active:scale-95'
                  }`}
                >
                  {isEnrolling ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : isEnrolled ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Active Student
                    </>
                  ) : (
                    <>
                      <CreditCard className="h-3.5 w-3.5" />
                      {!c.price || c.price === 0 ? 'Free Enrollment' : `Purchase Course ($${c.price})`}
                    </>
                  )}
                </button>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Checkout Modal */}
      <CheckoutModal
        isOpen={isCheckoutOpen}
        course={selectedCourseForCheckout}
        onClose={() => setIsCheckoutOpen(false)}
        onSuccess={() => {
          setIsCheckoutOpen(false);
          fetchCourses();
          if (selectedCourseForCheckout) {
            navigate(`/course/${selectedCourseForCheckout.id}`);
          }
        }}
      />
    </div>
  );
};
export default EnrollCourse;
