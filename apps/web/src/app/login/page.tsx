'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { getSupabasePublicConfig } from '@/lib/supabase/env';
import { sanitizeNextPath } from '@/lib/auth/redirect';

const RESEND_COOLDOWN_SECONDS = 60;

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = sanitizeNextPath(searchParams.get('next'), '/opportunities');
  const urlError = searchParams.get('error');
  const isConfigured = Boolean(getSupabasePublicConfig());

  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [loadingGoogle, setLoadingGoogle] = useState(false);
  const [loadingOtp, setLoadingOtp] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    urlError ? 'Authentication could not be completed. Please try again.' : null
  );
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  async function handleGoogleLogin() {
    if (!isConfigured) {
      setErrorMessage('Supabase public environment variables are not configured.');
      return;
    }
    setErrorMessage(null);
    setStatusMessage(null);
    setLoadingGoogle(true);
    try {
      const supabase = createClient();
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(nextPath)}`;
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo },
      });
      if (error) {
        setErrorMessage(error.message);
        setLoadingGoogle(false);
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Google sign-in failed.');
      setLoadingGoogle(false);
    }
  }

  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    if (!isConfigured) {
      setErrorMessage('Supabase public environment variables are not configured.');
      return;
    }
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    setErrorMessage(null);
    setStatusMessage(null);
    setLoadingOtp(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOtp({
        email: trimmedEmail,
        options: { shouldCreateUser: true },
      });
      if (error) {
        setErrorMessage(error.message);
        return;
      }
      setStep('otp');
      setCooldown(RESEND_COOLDOWN_SECONDS);
      setStatusMessage(`A 6-digit verification code has been sent to ${trimmedEmail}.`);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to send verification code.');
    } finally {
      setLoadingOtp(false);
    }
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    const cleanedOtp = otp.replace(/\D/g, '').slice(0, 6);
    if (cleanedOtp.length !== 6) {
      setErrorMessage('Enter the 6-digit verification code from your email.');
      return;
    }

    setErrorMessage(null);
    setStatusMessage(null);
    setLoadingOtp(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: cleanedOtp,
        type: 'email',
      });
      if (error) {
        setErrorMessage(error.message);
        return;
      }
      setStatusMessage('Signed in successfully. Redirecting...');
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Verification failed.');
    } finally {
      setLoadingOtp(false);
    }
  }

  async function handleResendOtp() {
    if (cooldown > 0 || loadingOtp || !isConfigured) return;
    setErrorMessage(null);
    setStatusMessage(null);
    setLoadingOtp(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true },
      });
      if (error) {
        setErrorMessage(error.message);
        return;
      }
      setCooldown(RESEND_COOLDOWN_SECONDS);
      setStatusMessage(`A new 6-digit verification code was sent to ${email.trim()}.`);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to resend code.');
    } finally {
      setLoadingOtp(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6 bg-slate-950 text-slate-100">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl space-y-6">
        <div className="space-y-2 text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            NexteRaS / Opportunity OS
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Sign in to your account</h1>
          <p className="text-sm text-slate-400">
            Continue with Google or verify with a 6-digit email code.
          </p>
        </div>

        {!isConfigured && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-300">
            Authentication is awaiting <code>NEXT_PUBLIC_SUPABASE_URL</code> and{' '}
            <code>NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY</code> configuration.
          </div>
        )}

        {errorMessage && (
          <div
            role="alert"
            className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
          >
            {errorMessage}
          </div>
        )}

        {statusMessage && (
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
            {statusMessage}
          </div>
        )}

        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={loadingGoogle || loadingOtp || !isConfigured}
          className="w-full flex items-center justify-center gap-3 rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 hover:bg-slate-100 disabled:opacity-50 transition"
        >
          <span>{loadingGoogle ? 'Redirecting to Google...' : 'Continue with Google'}</span>
        </button>

        <div className="relative flex items-center py-1">
          <div className="flex-grow border-t border-slate-800" />
          <span className="mx-3 text-xs uppercase tracking-wider text-slate-500">or</span>
          <div className="flex-grow border-t border-slate-800" />
        </div>

        {step === 'email' ? (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={loadingOtp || loadingGoogle || !isConfigured}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {loadingOtp ? 'Sending code...' : 'Continue with Email'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="otp" className="block text-sm font-medium text-slate-300">
                6-digit verification code
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-center text-lg font-mono tracking-[0.4em] text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={loadingOtp || otp.length !== 6}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {loadingOtp ? 'Verifying...' : 'Verify 6-digit code'}
            </button>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <button
                type="button"
                onClick={() => {
                  setStep('email');
                  setOtp('');
                  setErrorMessage(null);
                  setStatusMessage(null);
                }}
                className="hover:text-slate-200 underline"
              >
                Change email
              </button>
              <button
                type="button"
                disabled={cooldown > 0 || loadingOtp}
                onClick={handleResendOtp}
                className="hover:text-slate-200 disabled:opacity-50"
              >
                {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code'}
              </button>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
          Loading sign-in...
        </main>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
