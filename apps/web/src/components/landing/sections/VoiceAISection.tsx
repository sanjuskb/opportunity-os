'use client';

import React from 'react';
import { Mic, Sparkles, Volume2, Radio, CheckCircle2 } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export function VoiceAISection() {
  return (
    <section id="voice-ai" className="py-20 border-t border-slate-800/80 bg-[#090D16] relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row-reverse items-center justify-between gap-12">
          {/* Section Narrative */}
          <div className="w-full lg:w-1/2 space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-violet-500/10 text-violet-300 border border-violet-500/25">
              <Radio className="h-3.5 w-3.5 text-violet-400 animate-pulse" />
              <span>Voice-First Architecture</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Speak in Your Mother Tongue. Discover Your Future.
            </h2>

            <p className="text-base text-slate-300 leading-relaxed">
              Designed specifically for students across India. Explore job qualifications, ask career questions, and practice mock interviews using natural speech in 7 native languages.
            </p>

            {/* Language grid */}
            <div className="flex flex-wrap gap-2 pt-1">
              {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                <div
                  key={lang.code}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 text-xs font-medium text-slate-300"
                >
                  <Volume2 className="h-3.5 w-3.5 text-violet-400" />
                  <span>{lang.name}</span>
                  <span className="text-[11px] text-slate-400">({lang.native})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Visual Showcase Card (Voice Animation Spline Integration Boundary) */}
          <div className="w-full lg:w-1/2">
            <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-[#0B0F19] p-6 shadow-2xl overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-violet-400 animate-ping" />
                  <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Acoustic Wave Feedback
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Web Audio + WebSockets
                </span>
              </div>

              {/* Harmonic Wave Representation */}
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
                <div className="relative flex items-center justify-center">
                  <div className="h-24 w-24 rounded-full bg-violet-600/20 border border-violet-500/40 flex items-center justify-center shadow-lg shadow-violet-500/20 animate-pulse">
                    <Mic className="h-10 w-10 text-violet-300" />
                  </div>
                  <div className="absolute -inset-2 rounded-full border border-violet-500/20 animate-ping" />
                </div>

                <div className="space-y-1">
                  <div className="text-sm font-bold text-white">Voice Interaction Animation Model</div>
                  <div className="text-xs text-slate-400 max-w-sm">
                    Harmonic wave shader driven by Web Audio API and AudioWorklet amplitude streams.
                  </div>
                </div>

                <div className="inline-flex items-center gap-1.5 text-xs text-violet-300 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 text-violet-400" />
                  <span>14-State Voice Lifecycle • Lazy-loaded • Native Mic Input</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
