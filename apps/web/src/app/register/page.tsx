'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { GraduationCap, Building2, School } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { createClient } from '@/lib/supabase/client';
import { getSupabasePublicConfig } from '@/lib/supabase/env';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';

export default function RegisterPage() {
  const router = useRouter();
  const isConfigured = Boolean(getSupabasePublicConfig());
  const { userRole, setUserRole, setActiveLanguage } = useMockStore();

  const [step, setStep] = useState<'form' | 'otp'>('form');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [language, setLanguage] = useState<string>(APP_CONFIG.DEFAULT_LANGUAGE);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!isConfigured) {
      setErrorMsg('Supabase public credentials are not configured.');
      return;
    }
    setIsLoading(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: {
          shouldCreateUser: true,
          data: { full_name: fullName.trim(), preferred_language: language, user_role: userRole },
        },
      });
      if (error) {
        setErrorMsg(error.message);
        return;
      }
      setActiveLanguage(language as typeof APP_CONFIG.DEFAULT_LANGUAGE);
      setStep('otp');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLoading(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: otp.trim(),
        type: 'email',
      });
      if (error) {
        setErrorMsg(error.message);
        return;
      }
      router.push('/onboarding');
      router.refresh();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'OTP verification failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[320px] bg-cyan-600/10 blur-[130px] rounded-full pointer-events-none" />

      <div className="w-full max-w-lg space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/20 border border-indigo-500/40">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
            </div>
            <span className="text-2xl font-black tracking-tight text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </span>
          </Link>
          <h1 className="text-xl font-bold tracking-tight text-white">Create Your Account</h1>
          <p className="text-xs text-slate-400">
            Discover internships and fellowships across 9 Indian regional languages.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2 p-1 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <button
            type="button"
            onClick={() => setUserRole('student')}
            className={`flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-xs font-semibold transition ${
              userRole === 'student'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <GraduationCap className="h-4 w-4" />
            <span>Student</span>
          </button>
          <button
            type="button"
            onClick={() => setUserRole('company')}
            className={`flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-xs font-semibold transition ${
              userRole === 'company'
                ? 'bg-blue-950 text-blue-300 border border-blue-800'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Building2 className="h-4 w-4" />
            <span>Company</span>
          </button>
          <button
            type="button"
            onClick={() => setUserRole('university')}
            className={`flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-xs font-semibold transition ${
              userRole === 'university'
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <School className="h-4 w-4" />
            <span>University</span>
          </button>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 shadow-2xl space-y-4">
          {errorMsg && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 p-3 text-xs text-rose-200">
              {errorMsg}
            </div>
          )}

          {step === 'form' ? (
            <form onSubmit={handleSendOtp} className="space-y-4">
              <Input
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="Sanju S. Kumar"
              />
              <Input
                label="College or Organization Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="name@college.edu.in"
              />
              <Select
                label="Preferred Operating & Voice Language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                options={APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => ({
                  value: l.code,
                  label: `${l.name} (${l.native})`,
                }))}
              />
              <Button type="submit" variant="glow" size="md" className="w-full" isLoading={isLoading}>
                <span>Send 6-Digit Verification Code</span>
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <p className="text-xs text-slate-300">
                Enter the 6-digit verification code sent to <span className="text-cyan-300">{email}</span>.
              </p>
              <Input
                label="Verification Code"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                placeholder="123456"
              />
              <Button type="submit" variant="glow" size="md" className="w-full" isLoading={isLoading}>
                <span>Verify & Continue to Onboarding</span>
              </Button>
            </form>
          )}

          <p className="text-center text-xs text-slate-400">
            Already registered?{' '}
            <Link href="/login" className="text-cyan-400 hover:underline font-semibold">
              Sign in with Email or Google
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
