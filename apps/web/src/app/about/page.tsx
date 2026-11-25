import React from 'react';
import Link from 'next/link';
import { LandingNavbar } from '../../components/landing/navigation/LandingNavbar';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Sparkles, ShieldCheck, Heart, ArrowRight } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col">
      <LandingNavbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <Badge variant="cyan">Our Mission & Ethos</Badge>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Leveling the Playing Field for 40M+ Indian College Students
          </h1>
          <p className="text-base text-slate-300 leading-relaxed">
            NexteRaS (The Upcoming Era.) is an AI-powered career intelligence and autonomous employability system built to solve the fragmented, opaque, and English-biased internship ecosystem across Tier 1, 2, and 3 Indian institutions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-3">
            <h2 className="text-lg font-bold text-cyan-400">Voice-First in 7 Languages</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Language should never be a barrier to career discovery. We natively support Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and English speech.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-3">
            <h2 className="text-lg font-bold text-emerald-400">Zero Hallucinations</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Every match is grounded by deterministic pre-checks against AICTE/UGC credentials, graduation batches, and verifiable GitHub project commits.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-3">
            <h2 className="text-lg font-bold text-violet-400">Autonomous Shuttles</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              AI agents continuously scour the web, evaluate applicant tracking rubrics, and prepare tailored applications while preserving human approval.
            </p>
          </div>
        </div>

        <div className="text-center pt-8">
          <Link href="/register">
            <Button variant="glow" size="lg">
              <span>Join NexteRaS</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        NexteRaS • AI Career Intelligence &amp; Autonomous Employability System • Apache-2.0
      </footer>
    </div>
  );
}
