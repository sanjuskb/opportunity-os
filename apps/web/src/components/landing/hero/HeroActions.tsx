'use client';

import React from 'react';
import Link from 'next/link';
import { Mic, ArrowRight, ShieldCheck } from 'lucide-react';

export function HeroActions() {
  return (
    <div className="pt-2 space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* Primary Action Button */}
        <Link
          href="/opportunities"
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-500 hover:to-cyan-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 transition"
        >
          <span>Explore Opportunities</span>
          <ArrowRight className="h-4 w-4" />
        </Link>

        {/* Secondary Action: Career Passport */}
        <Link
          href="/career-passport"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-700 hover:border-slate-600 hover:text-white transition"
        >
          <span>Career Passport</span>
        </Link>

        {/* Voice Trigger Pill */}
        <a
          href="#voice-ai"
          className="inline-flex items-center gap-2 rounded-lg border border-violet-500/40 bg-violet-950/30 px-3.5 py-2.5 text-xs font-semibold text-violet-300 hover:bg-violet-900/40 hover:border-violet-400 transition"
        >
          <span className="flex h-2 w-2 rounded-full bg-violet-400 animate-ping" />
          <Mic className="h-3.5 w-3.5 text-violet-300" />
          <span>Voice Intelligence Demo</span>
        </a>
      </div>

      {/* Trust & Verification Footnote */}
      <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>AICTE & UGC Verification</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
          <span>Zero-Hallucination Matching</span>
        </div>
      </div>
    </div>
  );
}
