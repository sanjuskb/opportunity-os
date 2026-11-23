'use client';

import React from 'react';
import type { EcosystemRole } from './RoleSwitcher';
import { Eye, RotateCcw, Cpu, Sparkles } from 'lucide-react';

interface CampusHUDProps {
  activeHub: EcosystemRole | 'core';
  onReset: () => void;
  onSelectHub: (hub: EcosystemRole) => void;
}

const HUB_INFO: Record<
  EcosystemRole | 'core',
  { title: string; subtitle: string; color: string; badge: string; metrics: string }
> = {
  students: {
    title: 'Student Academy Hub',
    subtitle: 'Career Passports, Verified Skills, Resume Tailoring',
    color: '#06B6D4',
    badge: 'Cyan Sector',
    metrics: '94% ATS Match Rate',
  },
  companies: {
    title: 'Enterprise Corporate Hub',
    subtitle: 'Verified Job Postings, Direct Recruiter Telemetry',
    color: '#3B82F6',
    badge: 'Sapphire Sector',
    metrics: '1,200+ Active Roles',
  },
  universities: {
    title: 'Academic Rotunda Hub',
    subtitle: 'Degree Accreditation, Syllabus Alignment, Placement Cell',
    color: '#10B981',
    badge: 'Emerald Sector',
    metrics: '340+ Partner Colleges',
  },
  opportunities: {
    title: 'Opportunity Ingestion Hub',
    subtitle: 'Autonomous Web Scraping, Hackathons & Fellowships',
    color: '#F59E0B',
    badge: 'Amber Sector',
    metrics: '10k+ Live Opportunities',
  },
  core: {
    title: 'Central AI Intelligence Core',
    subtitle: 'Autonomous Agent Orchestration & Real-time Matching',
    color: '#8B5CF6',
    badge: 'Violet Core',
    metrics: '7 Native Languages',
  },
};

export function CampusHUD({ activeHub, onReset, onSelectHub }: CampusHUDProps) {
  const current = HUB_INFO[activeHub];

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-4 z-20">
      {/* Top Bar: Title & Controls */}
      <div className="flex items-center justify-between w-full pointer-events-auto">
        <div className="flex items-center gap-2 rounded-lg bg-slate-950/70 border border-slate-800/80 px-2.5 py-1.5 backdrop-blur-md text-xs text-slate-300">
          <Cpu className="h-3.5 w-3.5 text-violet-400" />
          <span className="font-semibold text-white">Architectural Maquette</span>
          <span className="text-slate-500">•</span>
          <span className="text-[11px] text-slate-400">Concept 4 + 1</span>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="flex items-center gap-1.5 rounded-lg bg-slate-950/70 border border-slate-800/80 px-2.5 py-1.5 backdrop-blur-md text-xs text-slate-300 hover:text-white hover:border-slate-700 transition"
          aria-label="Reset camera and selection"
        >
          <RotateCcw className="h-3.5 w-3.5 text-cyan-400" />
          <span>Reset Overview</span>
        </button>
      </div>

      {/* Bottom Floating Telemetry Card */}
      <div className="w-full max-w-sm pointer-events-auto rounded-xl border border-slate-800 bg-slate-950/85 p-3.5 shadow-2xl backdrop-blur-md space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 rounded-full animate-pulse"
              style={{ backgroundColor: current.color }}
            />
            <span className="text-xs font-bold text-white tracking-wide">{current.title}</span>
          </div>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-700/80 text-slate-300">
            {current.badge}
          </span>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">{current.subtitle}</p>

        <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[11px]">
          <span className="text-slate-400">Live Telemetry:</span>
          <span className="font-semibold text-slate-200 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-cyan-400" />
            {current.metrics}
          </span>
        </div>
      </div>
    </div>
  );
}
