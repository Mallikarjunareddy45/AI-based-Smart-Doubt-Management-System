import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, first_name: string, last_name: string, password: string, role_name?: 'student' | 'tutor') => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Recover active session on mount
  useEffect(() => {
    const bootstrapAuth = async () => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!accessToken) {
        setIsLoading(false);
        return;
      }
      
      try {
        // Retrieve profile details using token
        const response = await api.get<User>('/auth/me');
        setUser(response.data);
      } catch (err) {
        // If access token is expired, attempt token refresh cycle
        if (refreshToken) {
          try {
            const refreshResponse = await api.post('/auth/refresh', null, {
              params: { refresh_token: refreshToken }
            });
            const { access_token } = refreshResponse.data;
            localStorage.setItem('access_token', access_token);
            
            // Refetch user profile
            const userResponse = await api.get<User>('/auth/me');
            setUser(userResponse.data);
          } catch (refreshErr) {
            // Refresh failed, clean up session
            logout();
          }
        } else {
          logout();
        }
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
      
      // Fetch user profile
      const userResponse = await api.get<User>('/auth/me');
      setUser(userResponse.data);
      return userResponse.data;
    } catch (error) {
      setUser(null);
      throw error;
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
      
      // Auto login after registration
      return await login(email, password);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      api.post(`/auth/logout?refresh_token=${refreshToken}`).catch(() => {});
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
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
