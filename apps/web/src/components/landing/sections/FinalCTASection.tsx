'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, useScrollReveal } from '../../ui/ScrollReveal';
import { FinalCTABackground } from '../FinalCTABackground';

export function FinalCTASection() {
  const { ref, isRevealed } = useScrollReveal(0.1, true);

  return (
    <section
      ref={ref}
      className="relative py-32 lg:py-44 bg-[#080B10] overflow-hidden"
    >
      {/* Retrofuturistic 3D Horizon Grid, Particles & Liquid Glass Background */}
      <FinalCTABackground />

      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center relative z-10 space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono bg-white/[0.04] backdrop-blur-md text-slate-300 border border-white/[0.1] shadow-[0_0_20px_rgba(139,92,246,0.15)]">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span className="text-white font-medium font-sans">NexteRaS • The Upcoming Era.</span>
        </div>

        <h2 className="font-serif text-4xl sm:text-5xl lg:text-6xl text-white font-normal leading-[1.12] tracking-tight">
          <span className="block">
            <SplitTextReveal
              text="Enter the Upcoming Era"
              delayOffsetMs={60}
              charDelayMs={20}
              isRevealed={isRevealed}
            />
          </span>
          <span className="block italic font-serif text-cyan-300">
            <SplitTextReveal
              text="with NexteRaS."
              delayOffsetMs={260}
              charDelayMs={20}
              isRevealed={isRevealed}
            />
          </span>
        </h2>

        <p className="text-slate-300 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed drop-shadow-sm">
          AI Career Intelligence &amp; Autonomous Employability System. Verify your skills, tailor your resume with 94%+ ATS precision, and speak to your career copilot in 7 native languages.
        </p>

        <ScrollRevealCard delayMs={200} replay={true} className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/overview"
            className="inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-400 text-slate-950 font-semibold px-8 py-3.5 text-sm shadow-[0_0_28px_rgba(6,182,212,0.35)] hover:shadow-[0_0_40px_rgba(6,182,212,0.55)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 group"
          >
            <span>Launch NexteRaS</span>
            <ArrowRight className="h-4 w-4 text-slate-950 group-hover:translate-x-1 transition-transform" />
          </Link>

          <Link
            href="/opportunities"
            className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] hover:border-white/20 border border-white/[0.09] text-slate-200 font-medium px-6 py-3.5 text-sm hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 backdrop-blur-sm"
          >
            Explore 10k+ Opportunities
          </Link>
        </ScrollRevealCard>
      </div>
    </section>
  );
}
