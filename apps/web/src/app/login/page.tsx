'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowRight, ShieldCheck, Mail, KeyRound } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { getSupabasePublicConfig } from '@/lib/supabase/env';
import { sanitizeNextPath } from '@/lib/auth/redirect';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

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
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/20 border border-indigo-500/40 shadow-md">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
            </div>
            <span className="text-2xl font-black tracking-tight text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </span>
          </Link>
          <h1 className="text-xl font-bold tracking-tight text-white">Sign In to Your Workspace</h1>
          <p className="text-xs text-slate-400">
            Continue with Google or verify with a 6-digit Supabase Email OTP code.
          </p>
        </div>

        {/* Auth Card */}
        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 shadow-2xl space-y-5">
          {!isConfigured && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-300">
              Authentication is awaiting <code>NEXT_PUBLIC_SUPABASE_URL</code> and{' '}
              <code>NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY</code> configuration.
            </div>
          )}

          {errorMessage && (
            <div
              role="alert"
              className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-300"
            >
              {errorMessage}
            </div>
          )}

          {statusMessage && (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-300">
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
              <Input
                label="College or Organization Email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="name@college.edu.in"
              />

              <Button
                type="submit"
                variant="glow"
                size="md"
                className="w-full"
                isLoading={loadingOtp}
                disabled={loadingOtp || loadingGoogle || !isConfigured}
              >
                <Mail className="h-4 w-4" />
                <span>{loadingOtp ? 'Sending Code...' : 'Continue with Email OTP'}</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="otp"
                  className="block text-xs font-semibold uppercase tracking-wider text-slate-400"
                >
                  6-Digit Verification Code
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
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-center text-lg font-mono tracking-[0.4em] text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <Button
                type="submit"
                variant="glow"
                size="md"
                className="w-full"
                isLoading={loadingOtp}
                disabled={loadingOtp || otp.length !== 6}
              >
                <KeyRound className="h-4 w-4" />
                <span>{loadingOtp ? 'Verifying...' : 'Verify 6-Digit Code'}</span>
              </Button>

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

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-slate-800/80">
            <span>New to NexteRaS? </span>
            <Link href="/register" className="text-cyan-400 font-semibold hover:underline">
              Create an Account
            </Link>
          </div>
        </div>

        {/* Security & Verification Footnote */}
        <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>AICTE &amp; UGC Accredited Verification Network</span>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-[#090D16] text-slate-400 text-sm">
          Loading sign-in...
        </main>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
