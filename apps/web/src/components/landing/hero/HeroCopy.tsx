'use client';

import React from 'react';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { Sparkles } from 'lucide-react';

export function HeroCopy() {
  return (
    <div className="space-y-5 text-left">
      {/* Category & Track Tag */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 shadow-sm">
        <Sparkles className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
        <span>Homingo Hackathon Edition 01</span>
        <span className="text-slate-600">•</span>
        <span className="text-cyan-400 font-medium">Neural Transit Atlas</span>
      </div>

      {/* Main H1 Headline */}
      <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-[1.15]">
        The Connected{' '}
        <span className="bg-gradient-to-r from-cyan-400 via-indigo-300 to-violet-400 bg-clip-text text-transparent">
          Career Intelligence
        </span>{' '}
        Operating System
      </h1>

      {/* Narrative Subtitle */}
      <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-xl">
        Not a chatbot or static job board. Opportunity OS is an autonomous collegiate ecosystem connecting students, companies, universities, and verified opportunities through AI agent shuttles and real-time voice intelligence.
      </p>

      {/* 7 Native Languages Strip */}
      <div className="space-y-1.5 pt-1">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Supported in 7 Native Indian Languages:
        </div>
        <div className="flex flex-wrap gap-1.5">
          {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
            <span
              key={lang.code}
              className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:border-cyan-500/40 hover:text-cyan-300 transition"
            >
              {lang.name} <span className="text-[10px] text-slate-400 font-normal">({lang.native})</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
