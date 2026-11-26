'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { getSupabasePublicConfig } from '@/lib/supabase/env';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

export default function ForgotPasswordPage() {
  const isConfigured = Boolean(getSupabasePublicConfig());
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!isConfigured) {
      setErrorMsg('Supabase public configuration is not available in this environment.');
      return;
    }
    setSubmitting(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/auth/callback?next=/settings`,
      });
      if (error) {
        setErrorMsg(error.message);
        return;
      }
      setIsSubmitted(true);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to dispatch reset link.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      <div className="w-full max-w-md space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center gap-2">
            <span className="text-2xl font-black text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </span>
          </Link>
          <h1 className="text-xl font-bold text-white">Reset Your Password</h1>
          <p className="text-xs text-slate-400">Enter your registered email to receive a secure recovery link.</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 shadow-2xl space-y-4">
          {errorMsg && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 p-3 text-xs text-rose-200">
              {errorMsg}
            </div>
          )}

          {isSubmitted ? (
            <div className="text-center space-y-3 py-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-950/80 border border-emerald-500/40 text-emerald-400">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h2 className="text-sm font-bold text-white">Recovery Link Dispatched</h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                Check <span className="text-cyan-300">{email}</span> for password reset instructions.
              </p>
              <div className="pt-2">
                <Link href="/login">
                  <Button variant="secondary" size="sm" className="w-full">
                    Return to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Registered College / Corporate Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="name@college.edu.in"
              />
              <Button type="submit" variant="primary" size="md" className="w-full" isLoading={submitting}>
                <span>Send Recovery Instructions</span>
              </Button>
              <div className="text-center pt-2">
                <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Back to Sign In</span>
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
