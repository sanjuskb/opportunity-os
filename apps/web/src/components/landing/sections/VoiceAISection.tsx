'use client';

import React from 'react';
import { Mic, Volume2, Radio, CheckCircle2 } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export function VoiceAISection() {
  return (
    <section id="voice-ai" className="py-28 lg:py-36 border-b border-white/[0.06] bg-[#080B10] relative overflow-hidden">
      {/* Background Violet Glow */}
      <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-[600px] h-[350px] bg-violet-600/[0.06] blur-[150px] rounded-full pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row-reverse items-center justify-between gap-12 lg:gap-16">
          {/* Section Narrative */}
          <div className="w-full lg:w-1/2 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
              <span className="text-slate-500">Chapter 07</span>
              <span className="text-slate-600">/</span>
              <span className="text-violet-400 font-medium font-sans">Voice-First Architecture</span>
            </div>

            <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
              Speak in your mother tongue. Discover your future.
            </h2>

            <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
              Designed specifically for engineering students across India. Explore job qualifications, ask career questions, and practice mock interviews using natural speech in 7 native languages.
            </p>

            {/* Language grid */}
            <div className="flex flex-wrap gap-2 pt-2">
              {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                <div
                  key={lang.code}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/[0.08] bg-white/[0.02] text-xs font-medium text-slate-300 hover:border-violet-500/40 hover:text-violet-300 transition"
                >
                  <Volume2 className="h-3.5 w-3.5 text-violet-400" />
                  <span>{lang.name}</span>
                  <span className="text-[11px] text-slate-500 font-mono">({lang.native})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Visual Showcase Card */}
          <div className="w-full lg:w-1/2">
            <div className="relative rounded-2xl border border-violet-500/30 bg-[#0C101A] p-8 shadow-[0_0_50px_rgba(139,92,246,0.08)] overflow-hidden space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-violet-400 animate-ping" />
                  <span className="text-xs font-mono uppercase tracking-wider text-violet-300 font-semibold">
                    Acoustic Wave Feedback
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.08]">
                  Web Audio + WebSockets
                </span>
              </div>

              {/* Harmonic Wave Representation */}
              <div className="py-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="relative flex items-center justify-center">
                  <div className="h-24 w-24 rounded-full bg-violet-600/20 border border-violet-500/40 flex items-center justify-center shadow-lg shadow-violet-500/20">
                    <Mic className="h-10 w-10 text-violet-300 animate-pulse" />
                  </div>
                  <div className="absolute -inset-2 rounded-full border border-violet-500/20 animate-ping" />
                </div>

                <div className="space-y-1">
                  <div className="text-sm font-semibold text-white">Multilingual Voice Copilot</div>
                  <div className="text-xs text-slate-400 max-w-sm">
                    14-state acoustic lifecycle supporting real-time streaming speech transcription and localized Indic responses.
                  </div>
                </div>

                <div className="inline-flex items-center gap-1.5 text-xs text-violet-300 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 text-violet-400" />
                  <span>Native Mic Input • 7 Languages • Sub-second Latency</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
