'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, ShieldCheck, GraduationCap, Building2, School } from 'lucide-react';
import { useMockStore, UserRole } from '../../lib/mock-data/mockStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export default function RegisterPage() {
  const router = useRouter();
  const { userRole, setUserRole } = useMockStore();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [collegeOrCompany, setCollegeOrCompany] = useState('');
  const [degree, setDegree] = useState('B.Tech');
  const [language, setLanguage] = useState<string>(APP_CONFIG.DEFAULT_LANGUAGE);
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      router.push('/onboarding');
    }, 600);
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
            Join 50,000+ Indian students discovering internships across 7 regional languages.
          </p>
        </div>

        {/* Role Selector Tabs */}
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

        {/* Register Form Card */}
        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 shadow-2xl space-y-4">
          <form onSubmit={handleRegister} className="space-y-4">
            <Input
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="e.g. Sanju Kumar"
            />

            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="sanju@college.edu.in"
            />

            {userRole === 'student' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="College / University Name"
                  value={collegeOrCompany}
                  onChange={(e) => setCollegeOrCompany(e.target.value)}
                  required
                  placeholder="e.g. NIT Trichy"
                />
                <Select
                  label="Degree Program"
                  value={degree}
                  onChange={(e) => setDegree(e.target.value)}
                  options={[
                    { value: 'B.Tech', label: 'B.Tech / B.E.' },
                    { value: 'M.Tech', label: 'M.Tech / M.E.' },
                    { value: 'MCA', label: 'MCA' },
                    { value: 'B.Sc', label: 'B.Sc Computer Science' },
                    { value: 'Ph.D', label: 'Ph.D Scholar' },
                  ]}
                />
              </div>
            ) : (
              <Input
                label="Organization / Company Name"
                value={collegeOrCompany}
                onChange={(e) => setCollegeOrCompany(e.target.value)}
                required
                placeholder="e.g. Google India or IIT Madras"
              />
            )}

            <Select
              label="Preferred Language (UI & Voice)"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              options={APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => ({
                value: l.code,
                label: `${l.name} (${l.native})`,
              }))}
            />

            <Button type="submit" variant="glow" size="md" className="w-full mt-2" isLoading={isLoading}>
              <span>Complete Profile in Onboarding</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-slate-800">
            <span>Already have an account? </span>
            <Link href="/login" className="text-cyan-400 font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
