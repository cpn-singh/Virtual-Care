/**
 * Email OTP Verification Screen
 * Author: Security & Frontend Team
 *
 * Enforces email validation using a short-lived 6-digit numeric OTP.
 * Features a 60-second cooldown timer for resend requests to prevent abuse.
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, RefreshCw, KeyRound, ArrowRight, Sparkles, Check, Mail } from 'lucide-react';

export const VerifyOtpPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState<string>('');
  const [otp, setOtp] = useState<string>('');
  const [devOtp, setDevOtp] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string>('');
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [isResending, setIsResending] = useState<boolean>(false);
  const [cooldown, setCooldown] = useState<number>(60);

  useEffect(() => {
    const paramEmail = searchParams.get('email');
    if (paramEmail) {
      setEmail(paramEmail);
      // Fetch latest dev code if running in local development mode
      api.auth.getDevOtp(paramEmail)
        .then((res: any) => {
          if (res?.data?.dev_otp) {
            setDevOtp(res.data.dev_otp);
          }
        })
        .catch(() => {});
    }
  }, [searchParams]);

  // If email state changes, also query dev otp
  useEffect(() => {
    if (email && email.includes('@')) {
      api.auth.getDevOtp(email)
        .then((res: any) => {
          if (res?.data?.dev_otp) {
            setDevOtp(res.data.dev_otp);
          }
        })
        .catch(() => {});
    }
  }, [email]);

  // 60-second resend countdown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== 6) {
      setErrorMsg('Please enter all 6 digits of your verification code.');
      return;
    }

    setErrorMsg('');
    setSuccessMsg('');
    setIsVerifying(true);

    try {
      const response: any = await api.auth.verifyOtp({
        email: email.trim().toLowerCase(),
        otp: otp.trim(),
      });

      if (response?.data?.token && response?.data?.user) {
        setSuccessMsg('Email verified successfully! Logging you in...');
        login(response.data.token, response.data.user);

        setTimeout(() => {
          if (response.data.user.role === 'doctor') {
            navigate('/doctor/dashboard');
          } else if (response.data.user.role === 'admin') {
            navigate('/admin/dashboard');
          } else {
            navigate('/patient/dashboard');
          }
        }, 1200);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification failed. Please check the code and try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendOtp = async () => {
    if (cooldown > 0 || isResending) return;

    setErrorMsg('');
    setSuccessMsg('');
    setIsResending(true);

    try {
      const response: any = await api.auth.resendOtp({
        email: email.trim().toLowerCase(),
      });
      setSuccessMsg(response?.message || 'A fresh 6-digit code has been sent to your email.');
      if (response?.data?.dev_otp) {
        setDevOtp(response.data.dev_otp);
      }
      setCooldown(60);
    } catch (err: any) {
      setErrorMsg(err.message || 'Could not resend code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16">
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-teal-50 text-teal-700 rounded-2xl flex items-center justify-center mx-auto border border-teal-200">
            <KeyRound className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Enter Verification Code</h1>
          <p className="text-xs text-slate-500 leading-relaxed">
            We sent a 6-digit verification code to <br />
            <strong className="text-slate-800">{email || 'your email'}</strong>
          </p>
        </div>

        {/* Development Environment Helper Banner */}
        {devOtp ? (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs space-y-2.5">
            <div className="flex items-center justify-between text-amber-900 font-bold">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-amber-600" /> Development Mode Active
              </span>
              <span className="text-[10px] bg-amber-200 text-amber-900 px-2 py-0.5 rounded-full font-bold">
                Local Testing
              </span>
            </div>
            <p className="text-amber-800 text-[11px] leading-relaxed">
              Real outbound emails require SMTP credentials. In local development mode, your generated verification code is:
            </p>
            <div className="flex items-center justify-between bg-white border border-amber-300 rounded-xl px-3 py-2">
              <span className="font-mono text-lg font-black text-amber-900 tracking-widest">{devOtp}</span>
              <button
                type="button"
                onClick={() => setOtp(devOtp)}
                className="bg-amber-600 hover:bg-amber-700 text-white font-bold px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Auto-Fill Code</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5 text-xs text-slate-600 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <Mail className="w-4 h-4 text-slate-500" /> Email Delivery Notice
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              If SMTP credentials are not configured in <code className="font-mono text-slate-700 bg-slate-200/70 px-1 py-0.5 rounded">backend/.env</code>, check your Django server terminal where OTP codes are printed automatically, or click Resend below.
            </p>
          </div>
        )}

        {errorMsg && (
          <div className="bg-red-50 text-red-700 p-3 rounded-xl text-xs font-semibold">{errorMsg}</div>
        )}
        {successMsg && (
          <div className="bg-emerald-50 text-emerald-800 p-3 rounded-xl text-xs font-semibold">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleVerify} className="space-y-4">
          {!searchParams.get('email') && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">6-Digit Code</label>
            <input
              type="text"
              maxLength={6}
              required
              autoFocus
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              placeholder="123456"
              className="w-full text-center tracking-[0.5em] font-mono text-2xl font-bold border-2 border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-600"
            />
          </div>

          <button
            type="submit"
            disabled={isVerifying || otp.length !== 6}
            className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-xs"
          >
            <span>{isVerifying ? 'Verifying Code...' : 'Verify Email & Enter'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Didn't receive the email?</span>
          <button
            type="button"
            onClick={handleResendOtp}
            disabled={cooldown > 0 || isResending}
            className="text-teal-700 font-bold hover:underline disabled:text-slate-400 disabled:no-underline"
          >
            {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Code'}
          </button>
        </div>
      </div>
    </div>
  );
};
