'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sparkles, ArrowRight, ShieldCheck, GraduationCap, Building2, School } from 'lucide-react';
import { useMockStore, UserRole } from '../../lib/mock-data/mockStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';

export default function LoginPage() {
  const router = useRouter();
  const { userRole, setUserRole } = useMockStore();
  const [email, setEmail] = useState('sanju.kumar@college.edu.in');
  const [password, setPassword] = useState('password123');
  const [isLoading, setIsLoading] = useState(false);

  const handleRoleQuickFill = (role: UserRole) => {
    setUserRole(role);
    if (role === 'student') {
      setEmail('sanju.kumar@college.edu.in');
    } else if (role === 'company') {
      setEmail('recruiter@google.com');
    } else {
      setEmail('placement.officer@nitt.edu');
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      if (userRole === 'company') {
        router.push('/company/dashboard');
      } else if (userRole === 'university') {
        router.push('/university/dashboard');
      } else {
        router.push('/overview');
      }
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background Glow */}
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
            Voice-first collegiate career intelligence platform for Indian students & recruiters.
          </p>
        </div>

        {/* Role Perspective Quick Selector */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 text-center">
            Demo Quick-Fill by Role:
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleRoleQuickFill('student')}
              className={`flex items-center justify-center gap-1.5 p-2 rounded-lg border text-xs font-medium transition ${
                userRole === 'student'
                  ? 'border-cyan-500/60 bg-cyan-950/60 text-cyan-300'
                  : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white'
              }`}
            >
              <GraduationCap className="h-3.5 w-3.5" />
              <span>Student</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleQuickFill('company')}
              className={`flex items-center justify-center gap-1.5 p-2 rounded-lg border text-xs font-medium transition ${
                userRole === 'company'
                  ? 'border-blue-500/60 bg-blue-950/60 text-blue-300'
                  : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white'
              }`}
            >
              <Building2 className="h-3.5 w-3.5" />
              <span>Recruiter</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleQuickFill('university')}
              className={`flex items-center justify-center gap-1.5 p-2 rounded-lg border text-xs font-medium transition ${
                userRole === 'university'
                  ? 'border-emerald-500/60 bg-emerald-950/60 text-emerald-300'
                  : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white'
              }`}
            >
              <School className="h-3.5 w-3.5" />
              <span>Placement</span>
            </button>
          </div>
        </div>

        {/* Login Form Card */}
        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 shadow-2xl backdrop-blur-md space-y-4">
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label="College or Organization Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@college.edu.in"
            />

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Password</label>
                <Link href="/forgot-password" className="text-xs text-cyan-400 hover:underline">
                  Forgot?
                </Link>
              </div>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" variant="glow" size="md" className="w-full" isLoading={isLoading}>
              <span>Enter Workspace</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-slate-800/80">
            <span>Don&apos;t have an account? </span>
            <Link href="/register" className="text-cyan-400 font-semibold hover:underline">
              Create an Account
            </Link>
          </div>
        </div>

        {/* Security & Verification Footnote */}
        <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>AICTE & UGC Accredited Verification Network</span>
        </div>
      </div>
    </div>
  );
}
