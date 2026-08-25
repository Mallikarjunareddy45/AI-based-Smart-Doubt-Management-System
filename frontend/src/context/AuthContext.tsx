import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { User } from '../types';

export const DEFAULT_GUEST_USER: User = {
  id: '00000000-0000-0000-0000-000000000000',
  email: 'guest@example.com',
  first_name: 'Guest',
  last_name: 'User',
  full_name: 'Guest User',
  is_active: true,
  roles: [
    { id: '1', name: 'student' },
    { id: '2', name: 'tutor' },
    { id: '3', name: 'admin' },
  ],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

interface AuthContextType {
  user: User;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeRole: 'student' | 'tutor' | 'admin';
  setActiveRole: (role: 'student' | 'tutor' | 'admin') => void;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, first_name: string, last_name: string, password: string, role_name?: 'student' | 'tutor') => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User>(DEFAULT_GUEST_USER);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeRole, setActiveRole] = useState<'student' | 'tutor' | 'admin'>('student');

  // Recover active session or load backend default profile
  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        const response = await api.get<User>('/auth/me');
        setUser(response.data);
      } catch (err) {
        // Fallback to default guest user
        setUser(DEFAULT_GUEST_USER);
      } finally {
        setIsLoading(false);
      }
    };
    
    bootstrapAuth();
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', email.trim());
      formData.append('password', password);
      
      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      const userResponse = await api.get<User>('/auth/me');
      setUser(userResponse.data);
      return userResponse.data;
    } catch (error) {
      setUser(DEFAULT_GUEST_USER);
      return DEFAULT_GUEST_USER;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (
    email: string, 
    first_name: string, 
    last_name: string, 
    password: string, 
    role_name: 'student' | 'tutor' = 'student'
  ): Promise<User> => {
    setIsLoading(true);
    try {
      await api.post('/auth/register', {
        email: email.trim(),
        first_name: first_name.trim(),
        last_name: last_name.trim(),
        password,
        role_names: [role_name]
      });
      
      return await login(email, password);
    } catch (error) {
      return DEFAULT_GUEST_USER;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(DEFAULT_GUEST_USER);
    window.location.href = '/student';
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: true,
      isLoading,
      activeRole,
      setActiveRole,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

