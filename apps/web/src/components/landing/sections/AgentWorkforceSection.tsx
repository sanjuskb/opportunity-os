'use client';

import React from 'react';
import { Bot, FileText, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

export function AgentWorkforceSection() {
  return (
    <section id="ai-agents" className="py-28 lg:py-36 border-b border-white/[0.06] bg-[#07090D] relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16">
          {/* Section Narrative */}
          <div className="w-full lg:w-1/2 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-slate-500">Architecture</span>
              <span className="text-slate-600">/</span>
              <span className="text-violet-400 font-medium font-sans">Autonomous AI Agents</span>
            </div>

            <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
              AI agent shuttles continuously working for you.
            </h2>

            <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
              In Opportunity OS, AI is not a chatbot waiting for prompts. Autonomous geometric agents traverse the ecosystem conduits to continuously discover internships, compute ATS alignment, verify prerequisites, and prepare candidate packages.
            </p>

            <div className="space-y-4 pt-2">
              <div className="p-4 rounded-xl border border-white/[0.07] bg-white/[0.02] flex items-start gap-4">
                <FileText className="h-5 w-5 text-cyan-400 mt-1 shrink-0" />
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">Resume Intelligence Agent</div>
                  <div className="text-xs text-slate-400 leading-relaxed">
                    Calculates real-time ATS match scores and suggests grounded project bullet points matching live opportunity requirements.
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl border border-white/[0.07] bg-white/[0.02] flex items-start gap-4">
                <ShieldCheck className="h-5 w-5 text-emerald-400 mt-1 shrink-0" />
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">Eligibility Verification Agent</div>
                  <div className="text-xs text-slate-400 leading-relaxed">
                    Validates graduation year, CGPA, AICTE guidelines, and regional criteria prior to submission with human-in-the-loop confirmation.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Visual Showcase Card */}
          <div className="w-full lg:w-1/2">
            <div className="relative rounded-2xl border border-white/[0.09] bg-[#0A0E17] p-8 shadow-2xl overflow-hidden space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-cyan-400" />
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                    Agent Dispatcher Telemetry
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Real-Time Shuttles
                </span>
              </div>

              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                    <div>
                      <div className="text-xs font-semibold text-white">Shuttle #204: AI4Bharat NLP</div>
                      <div className="text-[11px] text-slate-400">Match score computed: 98% • Prerequisites verified</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400">Ready</span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                    <div>
                      <div className="text-xs font-semibold text-white">Shuttle #189: Google SWE Intern</div>
                      <div className="text-[11px] text-slate-400">Prerequisite check: CGPA $\ge 8.5$ met</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-amber-400">Drafting</span>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-violet-400 animate-pulse" />
                    <div>
                      <div className="text-xs font-semibold text-white">Shuttle #142: Zerodha Core Eng</div>
                      <div className="text-[11px] text-slate-400">Application package compiled with Career Passport</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-violet-400">Awaiting Auth</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
