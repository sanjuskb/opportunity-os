'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { GraduationCap, Building2, School, ArrowRight } from 'lucide-react';
import { useMockStore, UserRole } from '../../lib/mock-data/mockStore';

export default function RoleSelectionPage() {
  const router = useRouter();
  const { setUserRole } = useMockStore();

  const handleSelect = (role: UserRole) => {
    setUserRole(role);
    if (role === 'student') {
      router.push('/overview');
    } else if (role === 'company') {
      router.push('/company/dashboard');
    } else {
      router.push('/university/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      <div className="w-full max-w-3xl space-y-8 relative z-10 text-center">
        <div className="space-y-2">
          <Link href="/" className="inline-flex items-center gap-2">
            <span className="text-2xl font-black text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Select Your Ecosystem Role</h1>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            NexteRaS is customized for the distinct requirements of students, hiring companies, and colleges.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          {/* Student Role Card */}
          <div
            onClick={() => handleSelect('student')}
            className="group cursor-pointer rounded-2xl border border-slate-800 bg-[#0D1322] p-6 hover:border-cyan-500/50 hover:bg-cyan-950/15 transition shadow-xl space-y-3"
          >
            <div className="h-12 w-12 rounded-xl bg-cyan-950 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:scale-105 transition">
              <GraduationCap className="h-6 w-6" />
            </div>
            <h2 className="text-base font-bold text-white group-hover:text-cyan-300 transition">Student</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Verify eligibility, build Career Passport, customize ATS resumes, and voice-apply to verified Indian internships.
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-xs text-cyan-400 font-semibold">
              <span>Enter Student Hub</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Company Role Card */}
          <div
            onClick={() => handleSelect('company')}
            className="group cursor-pointer rounded-2xl border border-slate-800 bg-[#0D1322] p-6 hover:border-blue-500/50 hover:bg-blue-950/15 transition shadow-xl space-y-3"
          >
            <div className="h-12 w-12 rounded-xl bg-blue-950 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-105 transition">
              <Building2 className="h-6 w-6" />
            </div>
            <h2 className="text-base font-bold text-white group-hover:text-blue-300 transition">Company Recruiter</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Publish internships, review skill-verified Indian candidates, and manage AI-screened candidate pipelines.
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-xs text-blue-400 font-semibold">
              <span>Enter Recruiter Hub</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* University Role Card */}
          <div
            onClick={() => handleSelect('university')}
            className="group cursor-pointer rounded-2xl border border-slate-800 bg-[#0D1322] p-6 hover:border-emerald-500/50 hover:bg-emerald-950/15 transition shadow-xl space-y-3"
          >
            <div className="h-12 w-12 rounded-xl bg-emerald-950 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition">
              <School className="h-6 w-6" />
            </div>
            <h2 className="text-base font-bold text-white group-hover:text-emerald-300 transition">University / College</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track student placements, verify academic credentials via DigiLocker, and coordinate campus recruitment drives.
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
              <span>Enter Placement Hub</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
