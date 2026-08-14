import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

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
  is_published: boolean;
  price: number;
  sections: Section[];
}

interface Category {
  id: string;
  name: string;
}

export const CourseBuilder: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const [course, setCourse] = useState<Course | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states for Course metadata
  const [courseTitle, setCourseTitle] = useState('');
  const [courseDescription, setCourseDescription] = useState('');
  const [courseCategory, setCourseCategory] = useState('');
  const [coursePrice, setCoursePrice] = useState(0);
  const [coursePublished, setCoursePublished] = useState(false);

  // Form states for creating Section
  const [sectionTitle, setSectionTitle] = useState('');
  const [sectionDescription, setSectionDescription] = useState('');

  // Form states for creating Lesson
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [lessonTitle, setLessonTitle] = useState('');
  const [lessonType, setLessonType] = useState<'video' | 'pdf' | 'notes'>('video');
  const [lessonVideoUrl, setLessonVideoUrl] = useState('');
  const [lessonPdfUrl, setLessonPdfUrl] = useState('');
  const [lessonNotesContent, setLessonNotesContent] = useState('');
  const [lessonDuration, setLessonDuration] = useState(0);

  const fetchCourseDetails = async () => {
    try {
      const courseRes = await api.get(`/courses/${courseId}`);
      setCourse(courseRes.data);
      setCourseTitle(courseRes.data.title);
      setCourseDescription(courseRes.data.description || '');
      setCourseCategory(courseRes.data.category_id || '');
      setCoursePrice(courseRes.data.price);
      setCoursePublished(courseRes.data.is_published);
      
      const catRes = await api.get('/courses/categories');
      setCategories(catRes.data);
      setLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch course data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourseDetails();
  }, [courseId]);

  // Update Course Metadata
  const handleUpdateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.put(`/courses/${courseId}`, {
        title: courseTitle,
        description: courseDescription,
        category_id: courseCategory || null,
        price: coursePrice,
        is_published: coursePublished
      });
      alert('Course metadata updated successfully!');
    } catch (err) {}
  };

  // Create Section
  const handleCreateSection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionTitle) return;
    try {
      const res = await api.post('/courses/sections', {
        course_id: courseId,
        title: sectionTitle,
        description: sectionDescription || null,
        order: course ? course.sections.length : 0
      });
      if (course) {
        setCourse({
          ...course,
          sections: [...course.sections, { ...res.data, lessons: [] }]
        });
      }
      setSectionTitle('');
      setSectionDescription('');
    } catch (err) {}
  };

  // Delete Section
  const handleDeleteSection = async (id: string) => {
    if (!confirm('Are you sure you want to delete this section and all its lessons?')) return;
    try {
      await api.delete(`/courses/sections/${id}`);
      if (course) {
        setCourse({
          ...course,
          sections: course.sections.filter(s => s.id !== id)
        });
      }
    } catch (err) {}
  };

  // Create Lesson
  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSectionId || !lessonTitle) return;
    
    const payload = {
      section_id: activeSectionId,
      title: lessonTitle,
      lesson_type: lessonType,
      order: 0,
      video_url: lessonType === 'video' ? lessonVideoUrl : null,
      pdf_url: lessonType === 'pdf' ? lessonPdfUrl : null,
      notes_content: lessonType === 'notes' ? lessonNotesContent : null,
      duration_seconds: lessonDuration
    };

    try {
      const res = await api.post('/courses/lessons', payload);
      if (course) {
        const updatedSections = course.sections.map(sec => {
          if (sec.id === activeSectionId) {
            return {
              ...sec,
              lessons: [...sec.lessons, res.data]
            };
          }
          return sec;
        });
        setCourse({ ...course, sections: updatedSections });
      }
      // Reset lesson form
      setLessonTitle('');
      setLessonVideoUrl('');
      setLessonPdfUrl('');
      setLessonNotesContent('');
      setLessonDuration(0);
      setActiveSectionId(null);
    } catch (err) {}
  };

  // Delete Lesson
  const handleDeleteLesson = async (sectionId: string, id: string) => {
    if (!confirm('Are you sure you want to delete this lesson?')) return;
    try {
      await api.delete(`/courses/lessons/${id}`);
      if (course) {
        const updatedSections = course.sections.map(sec => {
          if (sec.id === sectionId) {
            return {
              ...sec,
              lessons: sec.lessons.filter(l => l.id !== id)
            };
          }
          return sec;
        });
        setCourse({ ...course, sections: updatedSections });
      }
    } catch (err) {}
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
        <Link to="/tutor" className="mt-4 rounded bg-indigo-600 px-4 py-2 hover:bg-indigo-700">
          Go back dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Course Creator Studio</span>
            <h1 className="text-3xl font-bold text-white">Syllabus Builder: {course.title}</h1>
          </div>
          <Link to="/tutor" className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 hover:text-white">
            ← Back to Dashboard
          </Link>
        </div>

        {/* Content Split */}
        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left Column: Metadata & Controls */}
          <div className="space-y-8 lg:col-span-1">
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
              <h2 className="text-lg font-bold text-white mb-4">Course Settings</h2>
              
              <form onSubmit={handleUpdateCourse} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Title</label>
                  <input
                    type="text"
                    value={courseTitle}
                    onChange={(e) => setCourseTitle(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</label>
                  <textarea
                    value={courseDescription}
                    onChange={(e) => setCourseDescription(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-4 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Category</label>
                  <select
                    value={courseCategory}
                    onChange={(e) => setCourseCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">Unassigned</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Price ($)</label>
                  <input
                    type="number"
                    value={coursePrice}
                    onChange={(e) => setCoursePrice(parseFloat(e.target.value) || 0)}
                    step="0.01"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-300">Publish to Catalog</span>
                  <input
                    type="checkbox"
                    checked={coursePublished}
                    onChange={(e) => setCoursePublished(e.target.checked)}
                    className="h-5 w-5 rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
                >
                  Save Settings
                </button>
              </form>
            </div>

            {/* Create Section Widget */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
              <h2 className="text-lg font-bold text-white mb-4">Add Course Section</h2>
              <form onSubmit={handleCreateSection} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Section Title</label>
                  <input
                    type="text"
                    value={sectionTitle}
                    onChange={(e) => setSectionTitle(e.target.value)}
                    placeholder="e.g. 'Intro to Python Data Types'"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Section Objective</label>
                  <input
                    type="text"
                    value={sectionDescription}
                    onChange={(e) => setSectionDescription(e.target.value)}
                    placeholder="Optional short subtitle"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full rounded-lg border border-indigo-600/30 bg-indigo-600/10 px-4 py-2.5 text-sm font-semibold text-indigo-400 hover:bg-indigo-600 hover:text-white transition-all"
                >
                  + Add Section
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Dynamic Course Syllabus Tree */}
          <div className="space-y-6 lg:col-span-2">
            <h2 className="text-2xl font-bold text-white">Course Syllabus Tree</h2>
            
            {course.sections.length === 0 ? (
              <div className="rounded-xl border-2 border-dashed border-slate-800 p-12 text-center text-slate-500">
                Syllabus is empty. Create a section on the left sidebar to start compiling course curriculum.
              </div>
            ) : (
              course.sections.map((section, sIdx) => (
                <div key={section.id} className="rounded-xl border border-slate-800 bg-slate-900/20 overflow-hidden">
                  {/* Section Title Banner */}
                  <div className="flex items-center justify-between bg-slate-900/60 px-6 py-4">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Section {sIdx + 1}</span>
                      <h3 className="text-lg font-bold text-white">{section.title}</h3>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setActiveSectionId(section.id)}
                        className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
                      >
                        + Add Lesson
                      </button>
                      <button
                        onClick={() => handleDeleteSection(section.id)}
                        className="text-xs text-red-500 hover:text-red-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Add Lesson Modal Overlay (Nested inside specific section) */}
                  {activeSectionId === section.id && (
                    <div className="border-b border-slate-800 bg-slate-900/40 p-6">
                      <h4 className="text-sm font-bold text-white mb-3">Add Lesson</h4>
                      <form onSubmit={handleCreateLesson} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs text-slate-500 mb-2">Lesson Title</label>
                            <input
                              type="text"
                              value={lessonTitle}
                              onChange={(e) => setLessonTitle(e.target.value)}
                              placeholder="e.g. 'Class Variables vs Instance Variables'"
                              className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-slate-500 mb-2">Lesson Type</label>
                            <select
                              value={lessonType}
                              onChange={(e) => setLessonType(e.target.value as any)}
                              className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                            >
                              <option value="video">Video Lesson</option>
                              <option value="pdf">PDF Lecture Notes</option>
                              <option value="notes">Rich Text Note</option>
                            </select>
                          </div>
                        </div>

                        {lessonType === 'video' && (
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-xs text-slate-500 mb-2">Video Resource Link (MP4/HLS)</label>
                              <input
                                type="text"
                                value={lessonVideoUrl}
                                onChange={(e) => setLessonVideoUrl(e.target.value)}
                                className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-slate-500 mb-2">Video Duration (seconds)</label>
                              <input
                                type="number"
                                value={lessonDuration}
                                onChange={(e) => setLessonDuration(parseInt(e.target.value) || 0)}
                                className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                              />
                            </div>
                          </div>
                        )}

                        {lessonType === 'pdf' && (
                          <div>
                            <label className="block text-xs text-slate-500 mb-2">PDF Document Link (URL)</label>
                            <input
                              type="text"
                              value={lessonPdfUrl}
                              onChange={(e) => setLessonPdfUrl(e.target.value)}
                              className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                            />
                          </div>
                        )}

                        {lessonType === 'notes' && (
                          <div>
                            <label className="block text-xs text-slate-500 mb-2">Markdown Note Content</label>
                            <textarea
                              value={lessonNotesContent}
                              onChange={(e) => setLessonNotesContent(e.target.value)}
                              rows={5}
                              className="w-full rounded bg-slate-950 border border-slate-700 p-3 text-sm text-slate-300 focus:outline-none"
                            />
                          </div>
                        )}

                        <div className="flex gap-3 justify-end mt-2">
                          <button
                            type="button"
                            onClick={() => setActiveSectionId(null)}
                            className="rounded bg-slate-800 px-4 py-1.5 text-xs text-slate-400 hover:text-slate-200"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="rounded bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
                          >
                            Save Lesson
                          </button>
                        </div>
                      </form>
                    </div>
                  )}

                  {/* Lessons Listing inside Section */}
                  <div className="divide-y divide-slate-800">
                    {section.lessons.length === 0 ? (
                      <div className="px-6 py-4 text-sm text-slate-500 italic">No lessons added to this section.</div>
                    ) : (
                      section.lessons.map((lesson) => (
                        <div key={lesson.id} className="flex items-center justify-between px-6 py-3 hover:bg-slate-900/30">
                          <div className="flex items-center gap-3">
                            <span className="text-xs uppercase bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                              {lesson.lesson_type}
                            </span>
                            <span className="text-sm font-medium text-slate-300">{lesson.title}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={async () => {
                                try {
                                  await api.post(`/quizzes/generate/lesson/${lesson.id}`);
                                  alert(`AI Quiz generated successfully for lesson: '${lesson.title}'!`);
                                } catch (err: any) {
                                  alert(err.response?.data?.detail || 'Failed to generate AI quiz.');
                                }
                              }}
                              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium border border-indigo-500/30 bg-indigo-950/40 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              ✨ Generate AI Quiz
                            </button>
                            <button
                              onClick={() => handleDeleteLesson(section.id, lesson.id)}
                              className="text-xs text-red-500 hover:text-red-400"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
