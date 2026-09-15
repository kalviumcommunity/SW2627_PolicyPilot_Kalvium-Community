'use client';
import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [isReady, setIsReady] = useState(false);

  const login = async (email, password) => {
    try {
      const resp = await axios.post('http://127.0.0.1:8000/auth/login', { email, password });
      const { access_token, role } = resp.data;
      localStorage.setItem('token', access_token);
      setUser({ email });
      setRole(role);
      return role;
    } catch (error) { throw error; }
  };

  const signup = async (name, email, password) => {
    const resp = await axios.post('http://127.0.0.1:8000/auth/signup', { name, email, password });
    const { access_token, role } = resp.data;
    localStorage.setItem('token', access_token);
    setUser({ email });
    setRole(role);
    return role;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setRole(null);
  };

  const loadUserFromToken = () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ email: payload.sub });
        setRole(payload.role);
      } catch {
        localStorage.removeItem('token');
      }
    }
    setIsReady(true);
  };

  useEffect(() => {
    loadUserFromToken();
  }, []);

  return (
    <AuthContext.Provider value={{ user, role, isReady, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => React.useContext(AuthContext);
