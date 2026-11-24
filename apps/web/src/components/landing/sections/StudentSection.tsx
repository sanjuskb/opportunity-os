'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, ArrowRight, CheckCircle2 } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, BackgroundChapterNo, useScrollReveal } from '../../ui/ScrollReveal';

export function StudentSection() {
  const { ref, isRevealed } = useScrollReveal(0.1);

  return (
    <section
      id="students"
      ref={ref}
      className="relative py-28 lg:py-36 border-b border-white/[0.06] bg-[#07090D] overflow-hidden"
    >
      {/* Massive Outlined Background Chapter Number */}
      <BackgroundChapterNo number="04" className="top-12 right-6 lg:right-16" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16">
          {/* Left Text */}
          <ScrollRevealCard delayMs={50} className="w-full lg:w-1/2">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
                <span className="text-slate-500">Chapter 04</span>
                <span className="text-slate-600">/</span>
                <span className="text-cyan-400 font-medium font-sans">For Students</span>
              </div>

              <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
                <SplitTextReveal
                  text="Your verified Career Passport & ATS Resume Studio."
                  delayOffsetMs={100}
                  charDelayMs={18}
                  isRevealed={isRevealed}
                />
              </h2>

              <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
                Never get rejected by opaque algorithms. Opportunity OS verifies your degree, marks, and projects directly via DigiLocker and GitHub, then tailors your resume with 94%+ ATS alignment.
              </p>

              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>AICTE & UGC DigiLocker accreditation directly attached to your profile.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>Explainable matching: know exactly which prerequisites you meet before applying.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>1-click application dispatch with honest audit trail tracking.</span>
                </div>
              </div>

              <div className="pt-4">
                <Link
                  href="/career-passport"
                  className="inline-flex items-center gap-2 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-5 py-2.5 text-xs font-semibold hover:bg-cyan-500/30 transition card-hover-lift group"
                >
                  <span>View Career Passport Demo</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition" />
                </Link>
              </div>
            </div>
          </ScrollRevealCard>

          {/* Right Tactile Card Demo */}
          <ScrollRevealCard delayMs={200} className="w-full lg:w-1/2">
            <div className="rounded-2xl border border-cyan-500/30 bg-[#0A101D] p-6 sm:p-8 space-y-6 shadow-[0_0_50px_rgba(6,182,212,0.08)] card-hover-lift">
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center font-bold text-cyan-300">
                    S
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">Sanju S. Kumar</div>
                    <div className="text-xs text-slate-400">NIT Tiruchirappalli • B.Tech CSE &apos;26</div>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  <ShieldCheck className="h-3.5 w-3.5" /> DigiLocker Verified
                </span>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1">
                  <div className="text-xs text-slate-400">Verified CGPA</div>
                  <div className="text-xl font-bold font-mono text-cyan-400">8.82 / 10</div>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1">
                  <div className="text-xs text-slate-400">ATS Resume Score</div>
                  <div className="text-xl font-bold font-mono text-emerald-400">94% Fit</div>
                </div>
              </div>

              {/* Match Radar Preview */}
              <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">Top Match: AI4Bharat NLP Research</span>
                  <span className="font-mono text-cyan-400 font-bold">98% Match</span>
                </div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Matched Skills: PyTorch, Transformers, Python, IndicNLP. Missing: Megatron-LM.
                </div>
              </div>
            </div>
          </ScrollRevealCard>
        </div>
      </div>
    </section>
  );
}
