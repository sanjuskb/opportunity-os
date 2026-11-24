'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, useScrollReveal } from '../../ui/ScrollReveal';

export function FinalCTASection() {
  const { ref, isRevealed } = useScrollReveal(0.1, true);

  return (
    <section
      ref={ref}
      className="relative py-32 lg:py-40 bg-[#080B10] overflow-hidden"
    >
      {/* Central AI Core Glow Callback */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-violet-600/[0.08] blur-[150px] rounded-full pointer-events-none" />

      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center relative z-10 space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
          <Sparkles className="h-3 w-3 text-violet-400" />
          <span className="text-white font-medium font-sans">The Future of Indian Tech Careers</span>
        </div>

        <h2 className="font-serif text-4xl sm:text-5xl lg:text-6xl text-white font-normal leading-[1.12] tracking-tight">
          <span className="block">
            <SplitTextReveal
              text="Enter the Connected Operating"
              delayOffsetMs={60}
              charDelayMs={20}
              isRevealed={isRevealed}
            />
          </span>
          <span className="block italic text-slate-200">
            <SplitTextReveal
              text="System."
              delayOffsetMs={260}
              charDelayMs={20}
              isRevealed={isRevealed}
            />
          </span>
        </h2>

        <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
          Built for the next generation of Indian engineers and builders. Verify your skills, tailor your resume with 94%+ ATS precision, and speak to your career copilot in 7 native languages.
        </p>

        <ScrollRevealCard delayMs={200} replay={true} className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/overview"
            className="inline-flex items-center gap-2 rounded-xl bg-white text-slate-950 font-semibold px-8 py-3.5 text-sm hover:bg-slate-200 shadow-[0_0_40px_rgba(255,255,255,0.2)] transition-all duration-200 card-hover-lift group"
          >
            <span>Launch Operating System</span>
            <ArrowRight className="h-4 w-4 text-slate-700 group-hover:translate-x-0.5 transition" />
          </Link>

          <Link
            href="/opportunities"
            className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.09] text-slate-300 font-medium px-6 py-3.5 text-sm transition-all duration-200 card-hover-lift"
          >
            Explore 10k+ Opportunities
          </Link>
        </ScrollRevealCard>
      </div>
    </section>
  );
}
