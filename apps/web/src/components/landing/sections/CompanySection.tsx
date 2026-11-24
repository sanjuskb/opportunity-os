'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, useScrollReveal } from '../../ui/ScrollReveal';
import { SpatialBackground } from '../SpatialBackground';

export function CompanySection() {
  const { ref, isRevealed } = useScrollReveal(0.1, true);

  return (
    <section
      id="companies"
      ref={ref}
      className="relative py-28 lg:py-36 border-b border-white/[0.06] bg-[#080B10] overflow-hidden"
    >
      {/* Architectural Spatial Geometry Background */}
      <SpatialBackground variant="pipeline" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col lg:flex-row-reverse items-center justify-between gap-12 lg:gap-16">
          {/* Right Text */}
          <ScrollRevealCard delayMs={50} replay={true} className="w-full lg:w-1/2">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
                <span className="text-blue-400 font-medium font-sans">For Companies</span>
              </div>

              <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
                <SplitTextReveal
                  text="Discover pre-screened engineering talent with zero spam."
                  delayOffsetMs={100}
                  charDelayMs={18}
                  isRevealed={isRevealed}
                />
              </h2>

              <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
                Stop sifting through 10,000 unverified PDF resumes. Filter candidate pools by institutionally verified CGPA, graduation batches, and demonstrable code repositories.
              </p>

              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Instant opportunity dispatch directly into verified student feeds.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Pre-screened candidates filtered by verified CGPA ≥ 8.0 and skill overlap.</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>1-click shortlisting and direct Career Passport inspection.</span>
                </div>
              </div>

              <div className="pt-4">
                <Link
                  href="/company/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-500/20 text-blue-300 border border-blue-500/40 px-5 py-2.5 text-xs font-semibold hover:bg-blue-500/30 transition card-hover-lift group"
                >
                  <span>Explore Recruiter Portal</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition" />
                </Link>
              </div>
            </div>
          </ScrollRevealCard>

          {/* Left Tactile Recruiter Pipeline Demo */}
          <ScrollRevealCard delayMs={200} replay={true} className="w-full lg:w-1/2">
            <div className="rounded-2xl border border-blue-500/30 bg-[#0A101D] p-6 sm:p-8 space-y-5 shadow-[0_0_50px_rgba(59,130,246,0.08)] card-hover-lift">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <div className="text-xs font-mono uppercase tracking-wider text-blue-400 font-semibold">
                  Live Candidate Discovery Pipeline
                </div>
                <span className="text-[11px] font-mono text-slate-400">142 Screened Candidates</span>
              </div>

              {/* Candidates Mock Feed with staggered items */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between card-hover-lift">
                  <div>
                    <div className="text-xs font-semibold text-white">Sanju S. Kumar</div>
                    <div className="text-[11px] text-slate-400">NIT Trichy • B.Tech CSE &apos;26 • CGPA: 8.82</div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">
                    94% Fit
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between card-hover-lift">
                  <div>
                    <div className="text-xs font-semibold text-white">Ananya Sharma</div>
                    <div className="text-[11px] text-slate-400">IIT Madras • B.Tech AI &apos;26 • CGPA: 9.15</div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">
                    96% Fit
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between card-hover-lift">
                  <div>
                    <div className="text-xs font-semibold text-white">Karthik Reddy</div>
                    <div className="text-[11px] text-slate-400">BITS Pilani • B.E. CS &apos;26 • CGPA: 8.65</div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">
                    89% Fit
                  </span>
                </div>
              </div>
            </div>
          </ScrollRevealCard>
        </div>
      </div>
    </section>
  );
}
