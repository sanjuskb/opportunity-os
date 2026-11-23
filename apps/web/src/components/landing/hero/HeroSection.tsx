'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { HeroCopy } from './HeroCopy';
import { RoleSwitcher, type EcosystemRole } from './RoleSwitcher';
import { HeroActions } from './HeroActions';
import { CampusFallback } from './CampusFallback';

// Dynamic import with ssr: false ensures zero SSR hydration mismatch and instant static fallback
const DynamicEcosystemCampus = dynamic(
  () =>
    import('../ecosystem/EcosystemCampus').then((mod) => mod.EcosystemCampus),
  {
    ssr: false,
    loading: () => <CampusFallback />,
  }
);

export function HeroSection() {
  const [activeRole, setActiveRole] = useState<EcosystemRole>('students');

  return (
    <section
      id="ecosystem-campus"
      className="relative min-h-[calc(100vh-4rem)] w-full flex items-center justify-center py-10 sm:py-14 lg:py-16 overflow-hidden"
    >
      {/* Background Ambience & Radial Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-600/10 blur-[130px] rounded-full pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[400px] h-[250px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-10 lg:gap-12">
          {/* Left Column: ~38% Composition */}
          <div className="w-full lg:w-[42%] xl:w-[38%] space-y-6 shrink-0 z-10">
            <HeroCopy />
            <RoleSwitcher activeRole={activeRole} onSelectRole={setActiveRole} />
            <HeroActions />
          </div>

          {/* Right Column: ~62% Composition (Interactive Architectural Maquette) */}
          <div className="w-full lg:w-[58%] xl:w-[62%] relative z-10">
            <DynamicEcosystemCampus
              activeRole={activeRole}
              onRoleChange={setActiveRole}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
