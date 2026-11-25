import React from 'react';
import { LandingNavbar } from '../components/landing/navigation/LandingNavbar';
import { HeroSection } from '../components/landing/hero/HeroSection';
import { ProblemSection } from '../components/landing/sections/ProblemSection';
import { UnifiedPlatformSection } from '../components/landing/sections/UnifiedPlatformSection';
import { StudentSection } from '../components/landing/sections/StudentSection';
import { CompanySection } from '../components/landing/sections/CompanySection';
import { UniversitySection } from '../components/landing/sections/UniversitySection';
import { AgentWorkforceSection } from '../components/landing/sections/AgentWorkforceSection';
import { VoiceAISection } from '../components/landing/sections/VoiceAISection';
import { FinalCTASection } from '../components/landing/sections/FinalCTASection';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300">
      {/* 1. Sticky Navigation with Live Chapter Tracker */}
      <LandingNavbar />

      {/* 2. Cinematic Narrative Chapters */}
      <main className="flex-1">
        {/* Chapter 01: The Ecosystem (Neural Transit Maquette) */}
        <HeroSection />

        {/* Chapter 02: The Problem / The Fragmentation */}
        <ProblemSection />

        {/* Chapter 03: The Unified Platform Architecture */}
        <UnifiedPlatformSection />

        {/* Chapter 04: For Students (Career Passport & ATS Resume Studio) */}
        <StudentSection />

        {/* Chapter 05: For Companies (High-Precision Recruitment Pipeline) */}
        <CompanySection />

        {/* Chapter 06: For Universities (Institutional Placement Intelligence) */}
        <UniversitySection />

        {/* AI Agent Workforce */}
        <AgentWorkforceSection />

        {/* Chapter 07: Voice-First Intelligence (7 Indic Languages) */}
        <VoiceAISection />

        {/* Chapter 08: Closing Call to Action */}
        <FinalCTASection />
      </main>

      {/* 3. Architectural Footer */}
      <footer className="border-t border-white/[0.06] bg-[#05070A] py-12 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-300">NexteRaS</span>
            <span>•</span>
            <span>The Upcoming Era.</span>
            <span>•</span>
            <span className="font-mono text-cyan-400">Team SyNtRax</span>
          </div>

          <div className="text-center sm:text-right text-slate-500 text-[11px] font-mono">
            <span>Neural Transit Atlas & Architectural Maquette</span>
            <span className="mx-2">•</span>
            <span>Apache-2.0 License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
