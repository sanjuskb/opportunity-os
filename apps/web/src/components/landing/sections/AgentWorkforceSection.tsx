'use client';

import React from 'react';
import { Bot, FileText, ShieldCheck, Sparkles } from 'lucide-react';
import { GenkubRobot } from '../GenkubRobot';
import { SplitTextReveal, ScrollRevealCard, BackgroundChapterNo, useScrollReveal } from '../../ui/ScrollReveal';

export function AgentWorkforceSection() {
  const { ref, isRevealed } = useScrollReveal(0.08);

  return (
    <section
      id="ai-agents"
      ref={ref}
      className="py-28 lg:py-36 border-b border-white/[0.06] bg-[#07090D] relative overflow-hidden"
    >
      {/* Background Subtle Cones */}
      <div className="absolute top-1/3 left-1/4 -translate-y-1/2 w-[600px] h-[350px] bg-violet-600/[0.05] blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[300px] bg-cyan-500/[0.04] blur-[140px] rounded-full pointer-events-none" />

      {/* Outlined Background Text */}
      <BackgroundChapterNo number="AI" className="top-10 right-8 lg:right-20" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16">
          {/* Section Narrative & Telemetry */}
          <ScrollRevealCard delayMs={50} className="w-full lg:w-1/2 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-slate-500">Autonomous Ecosystem</span>
              <span className="text-slate-600">/</span>
              <span className="text-violet-400 font-medium font-sans">AI Agent Workforce</span>
            </div>

            <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
              <SplitTextReveal
                text="AI agent shuttles continuously working for you."
                delayOffsetMs={100}
                charDelayMs={18}
                isRevealed={isRevealed}
              />
            </h2>

            <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
              In Opportunity OS, AI is not a passive chatbot waiting for text prompts. Autonomous geometric agent shuttles traverse ecosystem conduits to continuously ingest internships, compute ATS alignment, verify prerequisites, and prepare candidate packages.
            </p>

            <div className="space-y-3 pt-1">
              <div className="p-4 rounded-xl border border-white/[0.07] bg-white/[0.02] flex items-start gap-4 card-hover-lift">
                <FileText className="h-5 w-5 text-cyan-400 mt-1 shrink-0" />
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">Resume Intelligence Agent</div>
                  <div className="text-xs text-slate-400 leading-relaxed">
                    Calculates real-time ATS match scores and suggests grounded project bullet points matching live opportunity requirements.
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl border border-white/[0.07] bg-white/[0.02] flex items-start gap-4 card-hover-lift">
                <ShieldCheck className="h-5 w-5 text-emerald-400 mt-1 shrink-0" />
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">Eligibility Verification Agent</div>
                  <div className="text-xs text-slate-400 leading-relaxed">
                    Validates graduation year, CGPA, AICTE guidelines, and regional criteria prior to submission with human-in-the-loop confirmation.
                  </div>
                </div>
              </div>
            </div>

            {/* Live Shuttle Telemetry Feed */}
            <div className="p-4 rounded-2xl border border-white/[0.08] bg-[#0A0D15] space-y-3">
              <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>Active Agent Shuttles</span>
                <span className="text-emerald-400">3 In-Flight</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    <span>Shuttle #204: AI4Bharat NLP</span>
                  </span>
                  <span className="font-mono text-cyan-400">98% Match</span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                    <span>Shuttle #189: Google SWE Intern</span>
                  </span>
                  <span className="font-mono text-amber-400">Drafting</span>
                </div>
              </div>
            </div>
          </ScrollRevealCard>

          {/* Interactive Genkub Greeting Robot Feature Showcase */}
          <ScrollRevealCard delayMs={200} className="w-full lg:w-1/2">
            <GenkubRobot />
          </ScrollRevealCard>
        </div>
      </div>
    </section>
  );
}
