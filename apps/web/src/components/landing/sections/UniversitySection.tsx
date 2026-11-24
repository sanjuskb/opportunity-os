'use client';

import React from 'react';
import Link from 'next/link';
import { GraduationCap, ArrowRight, CheckCircle2 } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, BackgroundChapterNo, useScrollReveal } from '../../ui/ScrollReveal';

export function UniversitySection() {
  const { ref, isRevealed } = useScrollReveal(0.1);

  return (
    <section
      id="universities"
      ref={ref}
      className="relative py-28 lg:py-36 border-b border-white/[0.06] bg-[#07090D] overflow-hidden"
    >
      {/* Massive Outlined Background Chapter Number */}
      <BackgroundChapterNo number="06" className="top-12 right-6 lg:right-16" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16">
          {/* Left Text */}
          <ScrollRevealCard delayMs={50} className="w-full lg:w-1/2">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
                <span className="text-slate-500">Chapter 06</span>
                <span className="text-slate-600">/</span>
                <span className="text-emerald-400 font-medium font-sans">For Universities</span>
              </div>

              <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
                <SplitTextReveal
                  text="Empower your placement cell with verifiable career analytics."
                  delayOffsetMs={100}
                  charDelayMs={18}
                  isRevealed={isRevealed}
                />
              </h2>

              <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
                Automate collegiate placement tracking. Institutional placement officers securely sign and verify student semester marksheets via DigiLocker and track cohort readiness in real time.
              </p>

              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Cohort placement index & departmental placement readiness tracking.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Cryptographic credential verification gateway to sign student achievements.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Direct employer relationships and campus recruitment scheduling.</span>
                </div>
              </div>

              <div className="pt-4">
                <Link
                  href="/university/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-5 py-2.5 text-xs font-semibold hover:bg-emerald-500/30 transition card-hover-lift group"
                >
                  <span>View University Dashboard</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition" />
                </Link>
              </div>
            </div>
          </ScrollRevealCard>

          {/* Right Tactile Card Demo */}
          <ScrollRevealCard delayMs={200} className="w-full lg:w-1/2">
            <div className="rounded-2xl border border-emerald-500/30 bg-[#0A101D] p-6 sm:p-8 space-y-6 shadow-[0_0_50px_rgba(16,185,129,0.08)] card-hover-lift">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-400 font-semibold">
                  <GraduationCap className="h-4 w-4" /> NIT Tiruchirappalli Placement Cell
                </div>
                <span className="text-[11px] font-mono text-slate-400">Batch 2026</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1">
                  <div className="text-xs text-slate-400">Cohort Placement Index</div>
                  <div className="text-2xl font-bold font-mono text-emerald-400">82.4%</div>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-1">
                  <div className="text-xs text-slate-400">Average Verified Stipend</div>
                  <div className="text-2xl font-bold font-mono text-cyan-400">₹45,000/mo</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-1">
                <div className="text-xs font-semibold text-white">DigiLocker Signing Gateway</div>
                <div className="text-xs text-slate-400">32 student semester marksheets verified and signed today.</div>
              </div>
            </div>
          </ScrollRevealCard>
        </div>
      </div>
    </section>
  );
}
