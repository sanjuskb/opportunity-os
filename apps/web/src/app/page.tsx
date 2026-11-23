import React from 'react';
import { LandingNavbar } from '../components/landing/navigation/LandingNavbar';
import { HeroSection } from '../components/landing/hero/HeroSection';
import { AgentWorkforceSection } from '../components/landing/sections/AgentWorkforceSection';
import { VoiceAISection } from '../components/landing/sections/VoiceAISection';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Responsive Glass Navigation */}
      <LandingNavbar />

      {/* 2. Main Hero Section (Left 38% Copy/RoleSwitcher + Right 62% R3F Ecosystem Campus) */}
      <main className="flex-1">
        <HeroSection />

        {/* 3. Mid-Page Autonomous AI Agent Workforce Section */}
        <AgentWorkforceSection />

        {/* 4. Lower-Page Multilingual Voice AI Intelligence Section */}
        <VoiceAISection />
      </main>

      {/* 5. Production Landing Footer */}
      <footer className="border-t border-slate-800/80 bg-[#070A11] py-8 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-300">Opportunity OS</span>
            <span>•</span>
            <span>Homingo Hackathon Edition 01 (LLM Applications)</span>
          </div>

          <div className="text-center sm:text-right text-slate-500 text-[11px]">
            <span>Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)</span>
            <span className="mx-1.5">•</span>
            <span>Apache-2.0 License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
