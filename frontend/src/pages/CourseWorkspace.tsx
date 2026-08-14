import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { AITutorDrawer } from '../components/ai/AITutorDrawer';
import { QuizPlayerModal } from '../components/quiz/QuizPlayerModal';
import { AdaptiveRemediationCard } from '../components/quiz/AdaptiveRemediationCard';
import { Bot, Sparkles, Award, Play } from 'lucide-react';

interface Lesson {
  id: string;
  section_id: string;
  title: string;
  lesson_type: 'video' | 'pdf' | 'notes' | 'quiz' | 'coding' | 'assignment';
  order: number;
  video_url?: string;
  pdf_url?: string;
  notes_content?: string;
  duration_seconds: number;
  progress?: {
    is_completed: boolean;
    watch_time_seconds: number;
  };
  note?: {
    content: string;
  };
}

interface Section {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  order: number;
  lessons: Lesson[];
}

interface Course {
  id: string;
  code: string;
  title: string;
  description?: string;
  category_id?: string;
  instructor_id?: string;
  is_published: boolean;
  price: number;
  sections: Section[];
  enrollment_status?: string;
}

interface Bookmark {
  id: string;
  note?: string;
  timestamp_seconds: number;
  created_at: string;
}

export const CourseWorkspace: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const [course, setCourse] = useState<Course | null>(null);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Tabs: 'notes' | 'bookmarks' | 'details' | 'quizzes'
  const [activeTab, setActiveTab] = useState<'notes' | 'bookmarks' | 'details' | 'quizzes'>('notes');
  const [noteContent, setNoteContent] = useState('');
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [newBookmarkNote, setNewBookmarkNote] = useState('');

  // Quiz Player Modal state & list
  const [activeQuizId, setActiveQuizId] = useState<string | null>(null);
  const [isQuizModalOpen, setIsQuizModalOpen] = useState(false);
  const [quizzesList, setQuizzesList] = useState<any[]>([]);

  // AI Tutor Drawer & Video Timestamp state
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [currentTimestamp, setCurrentTimestamp] = useState<number | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const saveNoteTimeoutRef = useRef<any>(null);

  // Fetch course detailed syllabus
  const fetchCourseData = async () => {
    try {
      const res = await api.get(`/courses/${courseId}`);
      setCourse(res.data);
      if (res.data.sections.length > 0 && res.data.sections[0].lessons.length > 0) {
        // Set first lesson active by default
        const firstLesson = res.data.sections[0].lessons[0];
        setActiveLesson(firstLesson);
        setNoteContent(firstLesson.note?.content || '');
      }
      setLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch course syllabus');
      setLoading(false);
    }
  };

  const fetchCourseQuizzes = async () => {
    if (!courseId) return;
    try {
      const res = await api.get(`/quizzes/course/${courseId}`);
      setQuizzesList(res.data);
    } catch (err) {}
  };

  useEffect(() => {
    fetchCourseData();
    fetchCourseQuizzes();
  }, [courseId]);

  // Load bookmarks when active lesson changes
  useEffect(() => {
    if (activeLesson) {
      api.get(`/courses/lessons/${activeLesson.id}/bookmarks`)
        .then((res) => setBookmarks(res.data))
        .catch(() => {});
      setNoteContent(activeLesson.note?.content || '');
    }
  }, [activeLesson]);

  // Save progress (completion and watch time)
  const saveProgress = async (isCompleted: boolean, watchTime: number = 0) => {
    if (!activeLesson) return;
    try {
      await api.post(`/courses/lessons/${activeLesson.id}/progress`, {
        is_completed: isCompleted,
        watch_time_seconds: watchTime
      });
      // Update local state to show checkmark
      if (course) {
        const updatedSections = course.sections.map(sec => ({
          ...sec,
          lessons: sec.lessons.map(les => les.id === activeLesson.id ? {
            ...les,
            progress: { is_completed: isCompleted, watch_time_seconds: watchTime }
          } : les)
        }));
        setCourse({ ...course, sections: updatedSections });
      }
    } catch (err) {}
  };

  // Handle note change with auto-save debouncing
  const handleNoteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setNoteContent(val);

    if (saveNoteTimeoutRef.current) {
      clearTimeout(saveNoteTimeoutRef.current);
    }

    saveNoteTimeoutRef.current = setTimeout(async () => {
      if (!activeLesson) return;
      try {
        await api.post(`/courses/lessons/${activeLesson.id}/notes`, { content: val });
        // Update local cache
        if (course) {
          const updatedSections = course.sections.map(sec => ({
            ...sec,
            lessons: sec.lessons.map(les => les.id === activeLesson.id ? {
              ...les,
              note: { content: val }
            } : les)
          }));
          setCourse({ ...course, sections: updatedSections });
        }
      } catch (err) {}
    }, 1000);
  };

  // Add bookmark at current timestamp
  const handleAddBookmark = async () => {
    if (!activeLesson) return;
    let timestamp = 0;
    if (activeLesson.lesson_type === 'video' && videoRef.current) {
      timestamp = Math.floor(videoRef.current.currentTime);
    }
    
    try {
      const res = await api.post(`/courses/lessons/${activeLesson.id}/bookmarks`, {
        note: newBookmarkNote,
        timestamp_seconds: timestamp
      });
      setBookmarks([...bookmarks, res.data]);
      setNewBookmarkNote('');
    } catch (err) {}
  };

  // Delete bookmark
  const handleDeleteBookmark = async (id: string) => {
    try {
      await api.delete(`/courses/bookmarks/${id}`);
      setBookmarks(bookmarks.filter(b => b.id !== id));
    } catch (err) {}
  };

  const jumpToTimestamp = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play();
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-slate-900 text-white">
        <h1 className="text-2xl font-bold text-red-500">Error</h1>
        <p className="mt-2 text-slate-400">{error || 'Course not found'}</p>
        <Link to="/student" className="mt-4 rounded bg-indigo-600 px-4 py-2 hover:bg-indigo-700">
          Go back dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100 lg:flex-row">
      {/* Central Screen: Player/Viewer & Tabs */}
      <div className="flex flex-1 flex-col overflow-y-auto border-r border-slate-800">
        
        {/* Course Header Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/60 px-6 py-4 backdrop-blur-md">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">{course.code}</span>
            <h1 className="text-xl font-bold text-white">{course.title}</h1>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsAiDrawerOpen(!isAiDrawerOpen)}
              className="flex items-center gap-2 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30"
            >
              <Bot className="w-4 h-4" />
              <span>Ask AI Tutor</span>
              <Sparkles className="w-3 h-3 text-indigo-200" />
            </button>
            <Link to="/student" className="text-sm text-slate-400 hover:text-white">
              ← Exit Workspace
            </Link>
          </div>
        </div>

        {/* Dynamic Content Frame */}
        <div className="relative aspect-video w-full bg-black">
          {activeLesson ? (
            <>
              {activeLesson.lesson_type === 'video' && activeLesson.video_url && (
                <video
                  ref={videoRef}
                  src={activeLesson.video_url}
                  className="h-full w-full object-contain"
                  controls
                  onTimeUpdate={() => setCurrentTimestamp(videoRef.current ? Math.floor(videoRef.current.currentTime) : 0)}
                  onPlay={() => saveProgress(false, videoRef.current ? Math.floor(videoRef.current.currentTime) : 0)}
                  onPause={() => saveProgress(false, videoRef.current ? Math.floor(videoRef.current.currentTime) : 0)}
                  onEnded={() => saveProgress(true, activeLesson.duration_seconds)}
                />
              )}
              {activeLesson.lesson_type === 'pdf' && activeLesson.pdf_url && (
                <iframe
                  src={activeLesson.pdf_url}
                  className="h-full w-full border-0"
                  title="PDF Viewer"
                />
              )}
              {activeLesson.lesson_type === 'notes' && activeLesson.notes_content && (
                <div className="h-full overflow-y-auto bg-slate-900 px-8 py-6">
                  <div className="prose prose-invert max-w-none text-slate-300">
                    <h2 className="mb-4 text-2xl font-bold text-white">{activeLesson.title}</h2>
                    <p className="whitespace-pre-line">{activeLesson.notes_content}</p>
                  </div>
                  <div className="mt-8 flex justify-end">
                    <button
                      onClick={() => saveProgress(!activeLesson.progress?.is_completed)}
                      className={`rounded px-4 py-2 text-sm font-semibold transition-all ${
                        activeLesson.progress?.is_completed 
                          ? 'bg-emerald-600 text-white hover:bg-emerald-700' 
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'
                      }`}
                    >
                      {activeLesson.progress?.is_completed ? '✓ Lesson Completed' : 'Mark as Completed'}
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-slate-500">
              Select a lesson from the syllabus sidebar to begin.
            </div>
          )}
        </div>

        {/* Tabbed Workspace Section */}
        <div className="flex flex-1 flex-col bg-slate-900/40">
          <div className="flex border-b border-slate-800 bg-slate-900/60 px-6">
            <button
              onClick={() => setActiveTab('notes')}
              className={`border-b-2 px-4 py-3 text-sm font-medium transition-all ${
                activeTab === 'notes' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Notes Notepad
            </button>
            <button
              onClick={() => setActiveTab('bookmarks')}
              className={`border-b-2 px-4 py-3 text-sm font-medium transition-all ${
                activeTab === 'bookmarks' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Bookmarks
            </button>
            <button
              onClick={() => setActiveTab('details')}
              className={`border-b-2 px-4 py-3 text-sm font-medium transition-all ${
                activeTab === 'details' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Course Information
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`border-b-2 px-4 py-3 text-sm font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'quizzes' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Award className="w-4 h-4" />
              <span>Practice & AI Quizzes</span>
              {quizzesList.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-full text-[10px]">
                  {quizzesList.length}
                </span>
              )}
            </button>
          </div>

          <div className="flex-1 p-6">
            {activeTab === 'notes' && (
              <div className="h-full flex-col">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-300">Workspace study notes</h3>
                  <span className="text-xs text-slate-500">Autosaves notes to cloud...</span>
                </div>
                <textarea
                  value={noteContent}
                  onChange={handleNoteChange}
                  placeholder="Draft your learning notes here. These notes will persist next time you resume this lesson..."
                  className="h-48 w-full rounded-lg border border-slate-700 bg-slate-950 p-4 text-slate-300 placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            )}

            {activeTab === 'bookmarks' && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={newBookmarkNote}
                    onChange={(e) => setNewBookmarkNote(e.target.value)}
                    placeholder="Bookmark note (e.g. 'Recursion starts here')"
                    className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                  />
                  <button
                    onClick={handleAddBookmark}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                  >
                    Add Bookmark
                  </button>
                </div>

                <div className="mt-4 divide-y divide-slate-800">
                  {bookmarks.length === 0 ? (
                    <p className="py-4 text-sm text-slate-500">No bookmarks saved in this lesson.</p>
                  ) : (
                    bookmarks.map((bookmark) => (
                      <div key={bookmark.id} className="flex items-center justify-between py-3">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => jumpToTimestamp(bookmark.timestamp_seconds)}
                            className="rounded bg-slate-800 px-2.5 py-1 text-xs font-semibold text-indigo-400 hover:bg-indigo-900/50"
                          >
                            {Math.floor(bookmark.timestamp_seconds / 60)}:{(bookmark.timestamp_seconds % 60).toString().padStart(2, '0')}
                          </button>
                          <span className="text-sm text-slate-300">{bookmark.note || 'No description'}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteBookmark(bookmark.id)}
                          className="text-xs text-red-500 hover:text-red-400"
                        >
                          Remove
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'details' && (
              <div className="prose prose-invert max-w-none text-slate-300">
                <h3 className="text-lg font-bold text-white">About the Course</h3>
                <p>{course.description || 'No description provided.'}</p>
                <div className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 text-sm">
                  <div>
                    <span className="block text-slate-500">Price Model</span>
                    <span className="font-semibold text-white">{course.price === 0 ? 'Free tier access' : `$${course.price.toFixed(2)}`}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500">Instructor Ref</span>
                    <span className="font-semibold text-white">{course.instructor_id || 'AI Automated'}</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'quizzes' && (
              <div className="space-y-6">
                {/* Adaptive Remediation Analytics Widget */}
                <AdaptiveRemediationCard
                  courseId={course.id}
                  onStartAdaptiveQuiz={(qId) => {
                    setActiveQuizId(qId);
                    setIsQuizModalOpen(true);
                  }}
                  onSelectLesson={(lesId) => {
                    const found = course.sections.flatMap(s => s.lessons).find(l => l.id === lesId);
                    if (found) setActiveLesson(found);
                  }}
                />

                {/* Course Quizzes List */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Award className="w-4 h-4 text-indigo-400" /> Course Milestone Quizzes ({quizzesList.length})
                  </h3>

                  {quizzesList.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4">No milestone quizzes generated yet for this course.</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {quizzesList.map(qz => (
                        <div
                          key={qz.id}
                          className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between hover:border-slate-700 transition-colors"
                        >
                          <div>
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-400 block">
                              {qz.is_ai_generated ? 'AI Quiz' : 'Instructor Quiz'}
                            </span>
                            <h4 className="text-xs font-bold text-white mt-0.5">{qz.title}</h4>
                            <p className="text-[11px] text-slate-400 mt-1">Passing threshold: {qz.passing_score_percentage}%</p>
                          </div>
                          <button
                            onClick={() => {
                              setActiveQuizId(qz.id);
                              setIsQuizModalOpen(true);
                            }}
                            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1 shrink-0 transition-colors"
                          >
                            <Play className="w-3.5 h-3.5 fill-current" /> Start
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Sidebar: Syllabus Tree list */}
      <div className="w-full shrink-0 bg-slate-900 lg:w-96">
        <div className="border-b border-slate-800 bg-slate-900 px-6 py-4">
          <h2 className="text-lg font-bold text-white">Course Syllabus</h2>
          <p className="text-xs text-slate-400">Track and complete lessons sequentially</p>
        </div>

        <div className="divide-y divide-slate-800 overflow-y-auto">
          {course.sections.map((section, sIndex) => (
            <div key={section.id} className="bg-slate-900/20">
              <div className="px-6 py-3 bg-slate-900/60">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Section {sIndex + 1}</span>
                <h3 className="font-semibold text-white text-sm">{section.title}</h3>
                {section.description && <p className="text-xs text-slate-500 mt-0.5">{section.description}</p>}
              </div>

              <div className="py-2">
                {section.lessons.map((lesson) => (
                  <button
                    key={lesson.id}
                    onClick={() => setActiveLesson(lesson)}
                    className={`flex w-full items-center justify-between px-6 py-3 text-left transition-all ${
                      activeLesson?.id === lesson.id 
                        ? 'bg-indigo-600/20 border-l-4 border-indigo-500' 
                        : 'hover:bg-slate-800 border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {/* Checkmark icon for completion */}
                      <span className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[9px] font-bold ${
                        lesson.progress?.is_completed 
                          ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400' 
                          : 'border-slate-700 bg-slate-950 text-transparent'
                      }`}>
                        ✓
                      </span>
                      <div>
                        <span className="block text-xs font-semibold text-slate-300">{lesson.title}</span>
                        <span className="text-[10px] text-slate-500 capitalize">{lesson.lesson_type}</span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Floating RAG AI Tutor Drawer */}
      <AITutorDrawer
        isOpen={isAiDrawerOpen}
        onClose={() => setIsAiDrawerOpen(false)}
        courseId={course.id}
        activeLessonId={activeLesson?.id}
        activeLessonTitle={activeLesson?.title}
        currentTimestampSeconds={currentTimestamp}
        onJumpToTimestamp={jumpToTimestamp}
      />

      {/* Quiz Player Modal */}
      <QuizPlayerModal
        isOpen={isQuizModalOpen}
        quizId={activeQuizId}
        onClose={() => setIsQuizModalOpen(false)}
        onQuizCompleted={() => fetchCourseQuizzes()}
      />
    </div>
  );
};
