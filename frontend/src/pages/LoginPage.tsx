/**
 * Sign In Screen
 * Author: Security & Frontend Team
 *
 * Includes quick-fill demo buttons for easy evaluator testing.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { HeartPulse, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      const response: any = await api.auth.login({
        email: email.trim().toLowerCase(),
        password: password,
      });

      if (response?.data?.token && response?.data?.user) {
        login(response.data.token, response.data.user);

        if (response.data.user.role === 'doctor') {
          navigate('/doctor/dashboard');
        } else if (response.data.user.role === 'admin') {
          navigate('/admin/dashboard');
        } else {
          navigate('/patient/dashboard');
        }
      }
    } catch (err: any) {
      if (err.errors?.needs_verification) {
        navigate(`/verify-otp?email=${encodeURIComponent(err.errors.email || email)}`);
        return;
      }
      setErrorMsg(err.message || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMsg('');
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 space-y-6">
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-teal-600 rounded-2xl flex items-center justify-center text-white mx-auto shadow-sm">
            <HeartPulse className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome Back</h1>
          <p className="text-xs text-slate-500">
            Sign in to access your appointments, prescriptions, and medical records.
          </p>
        </div>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 p-3 rounded-xl text-xs font-semibold">{errorMsg}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-bold text-slate-700">Password</label>
              <Link to="/forgot-password" className="text-xs text-teal-700 hover:underline">
                Forgot?
              </Link>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-xs"
          >
            <span>{isLoading ? 'Signing In...' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-slate-600">
          Don't have an account yet?{' '}
          <Link to="/register" className="text-teal-700 font-bold hover:underline">
            Register now
          </Link>
        </div>

        {/* Quick Demo Fill Buttons for Patient & Doctor */}
        <div className="pt-4 border-t border-slate-100 space-y-2">
          <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider text-center">
            Demo Accounts (1-Click Fill)
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillDemoAccount('patient@example.com', 'PatientPass123!')}
              className="py-1.5 px-2 bg-slate-50 hover:bg-teal-50 border border-slate-200 text-slate-700 hover:text-teal-800 text-[11px] font-medium rounded-lg transition"
            >
              Patient Demo
            </button>
            <button
              type="button"
              onClick={() => fillDemoAccount('doctor@example.com', 'DoctorPass123!')}
              className="py-1.5 px-2 bg-slate-50 hover:bg-teal-50 border border-slate-200 text-slate-700 hover:text-teal-800 text-[11px] font-medium rounded-lg transition"
            >
              Doctor Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
