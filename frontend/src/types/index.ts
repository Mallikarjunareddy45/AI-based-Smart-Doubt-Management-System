// TypeScript data models matching Pydantic schemas

export interface Role {
  id: string;
  name: 'student' | 'tutor' | 'admin';
  description?: string;
}

export interface StudentProfile {
  matriculation_number?: string;
  profile_data?: Record<string, any>;
}

export interface TutorProfile {
  bio?: string;
  department?: string;
  max_workload: number;
  is_available: boolean;
}

export interface AdminProfile {
  department?: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  roles: Role[];
  student_profile?: StudentProfile;
  tutor_profile?: TutorProfile;
  admin_profile?: AdminProfile;
  created_at: string;
  updated_at: string;
}

export interface Course {
  id: string;
  code: string;
  title: string;
  description?: string;
  price?: number;
  created_at: string;
  updated_at: string;
}

export interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  status: 'active' | 'completed' | 'dropped';
  created_at: string;
  course?: Course;
}

export interface Question {
  id: string;
  student_id: string;
  course_id: string;
  cluster_id?: string;
  title: string;
  content: string;
  status: 'pending' | 'clustered' | 'resolved';
  urgency_score: number;
  priority_score: number;
  upvotes_count: number;
  assigned_tutor_name?: string;
  student_name?: string;
  student_email?: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionCluster {
  id: string;
  course_id: string;
  assigned_tutor_id?: string;
  status: 'pending' | 'assigned' | 'resolved';
  priority_score: number;
  summary?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  questions?: Question[];
}

export interface ChatMessage {
  id: string;
  cluster_id: string;
  sender_id: string;
  sender_name?: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface FileUpload {
  id: string;
  question_id?: string;
  message_id?: string;
  uploader_id: string;
  file_name: string;
  file_type: string;
  file_path: string;
  file_size: number;
  created_at: string;
}

export interface Notification {
  id: string;
  recipient_id: string;
  title: string;
  content: string;
  type: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}
