'use client';

import React, { useState, useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { SplitTextReveal } from '../../ui/ScrollReveal';

interface HeroCopyProps {
  activeRole: string;
  onSelectRole: (role: any) => void;
}

export function HeroCopy({ activeRole, onSelectRole }: HeroCopyProps) {
  // Above-the-fold entrance trigger: triggers on mount with graceful entrance
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsRevealed(true);
    }, 80);
    return () => clearTimeout(timer);
  }, []);

  const ROLES = [
    { id: 'students', label: 'Students', color: 'hover:text-cyan-400', active: 'text-cyan-300 border-cyan-500/50 bg-cyan-500/10' },
    { id: 'companies', label: 'Companies', color: 'hover:text-blue-400', active: 'text-blue-300 border-blue-500/50 bg-blue-500/10' },
    { id: 'universities', label: 'Universities', color: 'hover:text-emerald-400', active: 'text-emerald-300 border-emerald-500/50 bg-emerald-500/10' },
    { id: 'opportunities', label: 'Opportunities', color: 'hover:text-amber-400', active: 'text-amber-300 border-amber-500/50 bg-amber-500/10' },
  ];

  return (
    <div className="space-y-8 text-left relative z-10">
      {/* Discreet Platform Category Indicator */}
      <div className="flex items-center gap-2.5 text-xs font-mono text-slate-400">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
        <span className="text-slate-300 font-medium">Opportunity OS</span>
        <span className="text-slate-600">•</span>
        <span className="text-cyan-400 font-medium">Autonomous Career Intelligence</span>
      </div>

      {/* Main Editorial Headline with Character Reveal (Protected against mid-word break) */}
      <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-normal tracking-tight text-white leading-[1.08]">
        <span className="block">
          <SplitTextReveal
            text="The Connected"
            delayOffsetMs={40}
            charDelayMs={18}
            isRevealed={isRevealed}
          />
        </span>
        <span className="block italic font-serif text-cyan-300">
          <SplitTextReveal
            text="Career Intelligence"
            delayOffsetMs={240}
            charDelayMs={18}
            isRevealed={isRevealed}
          />
        </span>
        <span className="block">
          <SplitTextReveal
            text="Operating System."
            delayOffsetMs={520}
            charDelayMs={18}
            isRevealed={isRevealed}
          />
        </span>
      </h1>

      {/* Supporting Paragraph */}
      <p className="text-base sm:text-lg text-slate-400 font-normal leading-relaxed max-w-xl">
        An autonomous collegiate ecosystem interconnecting students, verified companies, universities, and live opportunities through neural agent shuttles and real-time voice intelligence.
      </p>

      {/* Restrained Perspective Selector */}
      <div className="space-y-2.5 pt-1">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
          Ecosystem Perspective:
        </div>
        <div className="flex flex-wrap gap-2">
          {ROLES.map((r) => (
            <button
              key={r.id}
              onClick={() => onSelectRole(r.id)}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all duration-200 ${
                activeRole === r.id
                  ? r.active
                  : 'border-white/[0.07] bg-white/[0.02] text-slate-400 hover:border-white/20 ' + r.color
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Primary & Secondary Actions with Refined Micro-Glow and Gentle Hover */}
      <div className="flex flex-wrap items-center gap-4 pt-1">
        <Link
          href="/overview"
          className="inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-cyan-400 via-cyan-300 to-sky-400 text-slate-950 font-semibold px-6 py-3 text-sm shadow-[0_0_24px_rgba(6,182,212,0.35)] hover:shadow-[0_0_35px_rgba(6,182,212,0.55)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 group"
        >
          <span>Enter Workspace</span>
          <ArrowRight className="h-4 w-4 text-slate-950 group-hover:translate-x-1 transition-transform" />
        </Link>

        <a
          href="#the-problem"
          className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] hover:border-white/20 border border-white/[0.08] text-slate-200 font-medium px-5 py-3 text-sm hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200"
        >
          Explore Ecosystem
        </a>
      </div>
    </div>
  );
}
