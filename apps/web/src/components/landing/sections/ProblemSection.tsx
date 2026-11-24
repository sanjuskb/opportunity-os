'use client';

import React from 'react';
import { XCircle, CheckCircle2 } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, useScrollReveal } from '../../ui/ScrollReveal';
import { SpatialBackground } from '../SpatialBackground';

export function ProblemSection() {
  const { ref, isRevealed } = useScrollReveal(0.1, true);

  return (
    <section
      id="the-problem"
      ref={ref}
      className="relative py-28 lg:py-36 border-b border-white/[0.06] bg-[#07090D] overflow-hidden"
    >
      {/* Architectural Spatial 3D Background */}
      <SpatialBackground variant="fragmented" />

      {/* Subtle Glow */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-[500px] h-[300px] bg-red-500/[0.03] blur-[140px] pointer-events-none" />
      <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-[500px] h-[300px] bg-cyan-500/[0.04] blur-[140px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="max-w-2xl mb-16 sm:mb-20 space-y-4">
          <div className="text-xs font-mono uppercase tracking-wider text-amber-400 font-semibold">
            The Fragmentation
          </div>

          <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.14]">
            <SplitTextReveal
              text="Why collegiate opportunities are broken across India."
              delayOffsetMs={80}
              charDelayMs={18}
              isRevealed={isRevealed}
            />
          </h2>

          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            Millions of ambitious engineering students, premier hiring teams, and placement cells operate in blind, disconnected silos.
          </p>
        </div>

        {/* Visual Architectural Comparison with Replaying Scroll Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Fragmented Reality */}
          <ScrollRevealCard delayMs={80} replay={true}>
            <div className="relative rounded-2xl border border-white/[0.07] bg-[#0A0D14]/70 p-8 sm:p-10 space-y-6 card-hover-lift h-full">
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                <span className="text-xs font-mono uppercase tracking-wider text-red-400 font-semibold flex items-center gap-2">
                  <XCircle className="h-4 w-4" /> The Disconnected Reality
                </span>
                <span className="text-[11px] font-mono text-slate-500">Legacy Systems</span>
              </div>

              <div className="space-y-4 text-sm text-slate-300">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                  <div className="font-semibold text-white">Scattered Black-Box Portals</div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Students submit hundreds of generic PDFs into automated ATS filters with 0% transparency or feedback.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                  <div className="font-semibold text-white">Unverified Skills & Grade Inflation</div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Companies spend months manually re-evaluating candidate qualifications that lack institutional verification.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-1">
                  <div className="font-semibold text-white">English-Only Linguistic Barrier</div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Brilliant technical builders in Tier-2/3 institutes are gated by lack of regional language career guidance.
                  </div>
                </div>
              </div>
            </div>
          </ScrollRevealCard>

          {/* Opportunity OS Solution */}
          <ScrollRevealCard delayMs={200} replay={true}>
            <div className="relative rounded-2xl border border-cyan-500/30 bg-[#0C121E]/80 p-8 sm:p-10 space-y-6 shadow-[0_0_50px_rgba(6,182,212,0.06)] card-hover-lift h-full">
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> The Connected Operating System
                </span>
                <span className="text-[11px] font-mono text-cyan-400/70">Neural Transit</span>
              </div>

              <div className="space-y-4 text-sm text-slate-200">
                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-1">
                  <div className="font-semibold text-white flex items-center gap-2">
                    <span>Cryptographic Career Passport</span>
                    <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">
                      AICTE / UGC
                    </span>
                  </div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Immutable digital credential backed by university DigiLocker marks, verified GitHub commits, and projects.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-1">
                  <div className="font-semibold text-white">Explainable Zero-Hallucination Matching</div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Every match explicitly details matched skills, missing prerequisites, and graduation batch criteria.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-1">
                  <div className="font-semibold text-white">Native Speech in 7 Indic Languages</div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    Voice interaction in Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and English.
                  </div>
                </div>
              </div>
            </div>
          </ScrollRevealCard>
        </div>
      </div>
    </section>
  );
}
