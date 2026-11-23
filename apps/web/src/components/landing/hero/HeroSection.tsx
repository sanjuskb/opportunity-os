'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { HeroCopy } from './HeroCopy';
import { CampusFallback } from './CampusFallback';
import type { EcosystemRole } from './RoleSwitcher';

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
      id="ecosystem"
      className="relative min-h-[calc(100vh-4rem)] w-full flex items-center justify-center pt-24 pb-16 lg:pt-28 lg:pb-24 overflow-hidden border-b border-white/[0.06]"
    >
      {/* Subtle Atmospheric Cones */}
      <div className="absolute top-1/4 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-violet-600/[0.07] blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[300px] bg-cyan-500/[0.05] blur-[140px] rounded-full pointer-events-none" />

      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16">
          {/* Left Column: ~42% Editorial Spatial Copy */}
          <div className="w-full lg:w-[45%] xl:w-[42%] shrink-0 z-10">
            <HeroCopy
              activeRole={activeRole}
              onSelectRole={(role) => setActiveRole(role as EcosystemRole)}
            />
          </div>

          {/* Right Column: ~58% Spacious 3D Architectural Maquette */}
          <div className="w-full lg:w-[55%] xl:w-[58%] relative z-10">
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
