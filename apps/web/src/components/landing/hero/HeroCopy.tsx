'use client';

import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { SplitTextReveal, useScrollReveal } from '../../ui/ScrollReveal';

interface HeroCopyProps {
  activeRole: string;
  onSelectRole: (role: any) => void;
}

export function HeroCopy({ activeRole, onSelectRole }: HeroCopyProps) {
  const { isRevealed } = useScrollReveal(0.05);

  const ROLES = [
    { id: 'students', label: 'Students', color: 'hover:text-cyan-400', active: 'text-cyan-300 border-cyan-500/50 bg-cyan-500/10' },
    { id: 'companies', label: 'Companies', color: 'hover:text-blue-400', active: 'text-blue-300 border-blue-500/50 bg-blue-500/10' },
    { id: 'universities', label: 'Universities', color: 'hover:text-emerald-400', active: 'text-emerald-300 border-emerald-500/50 bg-emerald-500/10' },
    { id: 'opportunities', label: 'Opportunities', color: 'hover:text-amber-400', active: 'text-amber-300 border-amber-500/50 bg-amber-500/10' },
  ];

  return (
    <div className="space-y-8 text-left relative z-10">
      {/* Chapter Marker */}
      <div className="inline-flex items-center gap-2.5 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08] transition-all duration-700">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
        <span className="text-slate-400">Chapter 01</span>
        <span className="text-slate-600">/</span>
        <span className="text-cyan-300 font-sans font-medium">Neural Transit Atlas</span>
      </div>

      {/* Main Editorial Headline with Character-by-Character Reveal (Homingo standard) */}
      <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-normal tracking-tight text-white leading-[1.08]">
        <SplitTextReveal
          text="The Connected "
          delayOffsetMs={50}
          charDelayMs={25}
          isRevealed={isRevealed}
        />
        <span className="italic font-serif text-slate-200">
          <SplitTextReveal
            text="Career Intelligence "
            delayOffsetMs={350}
            charDelayMs={25}
            isRevealed={isRevealed}
          />
        </span>
        <SplitTextReveal
          text="Operating System."
          delayOffsetMs={750}
          charDelayMs={25}
          isRevealed={isRevealed}
        />
      </h1>

      {/* Supporting Paragraph */}
      <p className="text-base sm:text-lg text-slate-400 font-normal leading-relaxed max-w-xl transition-opacity duration-1000 delay-500">
        An autonomous collegiate ecosystem interconnecting students, verified companies, universities, and live opportunities through neural agent shuttles and real-time voice intelligence.
      </p>

      {/* Restrained Perspective Selector */}
      <div className="space-y-2.5 pt-2">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
          Filter Atlas Perspective:
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

      {/* Primary & Secondary Actions with Micro Hover Lift */}
      <div className="flex flex-wrap items-center gap-4 pt-2">
        <Link
          href="/overview"
          className="inline-flex items-center gap-2 rounded-xl bg-white text-slate-950 font-semibold px-6 py-3 text-sm hover:bg-slate-200 shadow-[0_0_30px_rgba(255,255,255,0.15)] transition-all duration-200 card-hover-lift group"
        >
          <span>Enter Workspace</span>
          <ArrowRight className="h-4 w-4 text-slate-700 group-hover:translate-x-0.5 transition" />
        </Link>

        <a
          href="#the-problem"
          className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.09] text-slate-300 font-medium px-5 py-3 text-sm transition-all duration-200 card-hover-lift"
        >
          Read the Story
        </a>
      </div>
    </div>
  );
}
