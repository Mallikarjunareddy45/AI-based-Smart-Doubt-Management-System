import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthProvider } from './context/AuthContext';
import { SocketProvider } from './context/SocketContext';
import { ProtectedRoute, RoleGuard, DashboardRedirect } from './routes';
import { Layout } from './components/common/Layout';

// Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { StudentDashboard } from './pages/StudentDashboard';
import { TutorDashboard } from './pages/TutorDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { AskQuestion } from './pages/AskQuestion';
import { EnrollCourse } from './pages/EnrollCourse';
import { QuestionDetails } from './pages/QuestionDetails';
import { CourseWorkspace } from './pages/CourseWorkspace';
import { CourseBuilder } from './pages/CourseBuilder';

// Create React Query Client instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

import { useAuth } from './context/AuthContext';

export const RootRedirect: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return <Navigate to="/student" replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <SocketProvider>
            <Routes>
              {/* Direct Workspace Routes */}
              <Route path="/" element={<RootRedirect />} />
              <Route path="/login" element={<Navigate to="/student" replace />} />
              <Route path="/register" element={<Navigate to="/student" replace />} />
              <Route path="/landing" element={<Landing />} />

              {/* Workspace Layout */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<DashboardRedirect />} />
                
                {/* Student Workspace */}
                <Route path="/student" element={<Layout><StudentDashboard /></Layout>} />
                <Route path="/student/ask" element={<Layout><AskQuestion /></Layout>} />
                <Route path="/student/courses/enroll" element={<Layout><EnrollCourse /></Layout>} />
                <Route path="/student/courses/:courseId" element={<Layout><CourseWorkspace /></Layout>} />

                {/* Tutor Workspace */}
                <Route path="/tutor" element={<Layout><TutorDashboard /></Layout>} />
                <Route path="/tutor/courses/:courseId/edit" element={<Layout><CourseBuilder /></Layout>} />

                {/* Admin Workspace */}
                <Route path="/admin" element={<Layout><AdminDashboard /></Layout>} />

                {/* Shared Workspace routes */}
                <Route path="/questions/:questionId" element={<Layout><QuestionDetails /></Layout>} />
              </Route>

              {/* Fallback Redirection */}
              <Route path="*" element={<Navigate to="/student" replace />} />
            </Routes>
          </SocketProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
export default App;
