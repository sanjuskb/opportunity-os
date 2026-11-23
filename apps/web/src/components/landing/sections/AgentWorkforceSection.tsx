'use client';

import React from 'react';
import { Bot, Sparkles, CheckCircle2, Shield, Zap } from 'lucide-react';

export function AgentWorkforceSection() {
  return (
    <section id="agent-workforce" className="py-20 border-t border-slate-800/80 bg-[#080C15] relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
          {/* Section Narrative */}
          <div className="w-full lg:w-1/2 space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/25">
              <Bot className="h-3.5 w-3.5 text-blue-400" />
              <span>Autonomous AI Agents</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              AI Agent Shuttles Working for You
            </h2>

            <p className="text-base text-slate-300 leading-relaxed">
              In Opportunity OS, AI is not a chatbot waiting for prompts. Autonomous geometric agents traverse the ecosystem conduits to continuously discover internships, compute ATS alignment, verify prerequisites, and prepare candidate packages.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-white">
                  <Zap className="h-4 w-4 text-cyan-400" />
                  <span>Resume Intelligence Agent</span>
                </div>
                <p className="text-xs text-slate-400">
                  Calculates real-time ATS match scores and suggests project bullets matching live requirements.
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-white">
                  <Shield className="h-4 w-4 text-emerald-400" />
                  <span>Eligibility Verification Agent</span>
                </div>
                <p className="text-xs text-slate-400">
                  Validates graduation year, CGPA, AICTE guidelines, and regional criteria prior to submission.
                </p>
              </div>
            </div>
          </div>

          {/* Dedicated Visual Showcase Card (GENKUB Robot Integration Boundary) */}
          <div className="w-full lg:w-1/2">
            <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-[#0B0F19] p-6 shadow-2xl overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-400 animate-pulse" />
                  <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Agent Dispatcher Preview
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Spline Showcase Asset
                </span>
              </div>

              {/* Asset Reference & Verification State */}
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
                <div className="h-20 w-20 rounded-2xl bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center shadow-lg shadow-indigo-500/10">
                  <Bot className="h-10 w-10 text-cyan-400 animate-bounce" />
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-bold text-white">GENKUB Autonomous Agent Model</div>
                  <div className="text-xs text-slate-400 max-w-sm">
                    Isolated downstream lazy-load. Mounted exclusively when scrolled into viewport; zero impact on hero FCP.
                  </div>
                </div>
                <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium pt-2">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>311 KB Binary • Lazy-loaded • GPU Sandboxed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
