'use client';

import React from 'react';
import { Users, Building2, GraduationCap, Briefcase } from 'lucide-react';
import { SplitTextReveal, ScrollRevealCard, BackgroundChapterNo, useScrollReveal } from '../../ui/ScrollReveal';

export function UnifiedPlatformSection() {
  const { ref, isRevealed } = useScrollReveal(0.1);

  const CONDUITS = [
    {
      title: 'Student Hub',
      badge: 'Cyan Rail',
      icon: Users,
      color: 'text-cyan-400',
      border: 'border-cyan-500/30',
      bg: 'bg-cyan-950/20',
      desc: 'Autonomous profile curation, DigiLocker marks verification, and real-time ATS resume tailoring.',
    },
    {
      title: 'Company Hub',
      badge: 'Sapphire Rail',
      icon: Building2,
      color: 'text-blue-400',
      border: 'border-blue-500/30',
      bg: 'bg-blue-950/20',
      desc: 'Instant collegiate opportunity dispatch, pre-screened candidate discovery, and shortlist pipelines.',
    },
    {
      title: 'University Hub',
      badge: 'Emerald Rail',
      icon: GraduationCap,
      color: 'text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-950/20',
      desc: 'Placement cell analytics, cohort career readiness index, and institutional credential signing.',
    },
    {
      title: 'Live Opportunities',
      badge: 'Amber Rail',
      icon: Briefcase,
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-950/20',
      desc: 'Ingested high-stipend internships, research fellowships, and verified graduate opportunities.',
    },
  ];

  return (
    <section
      ref={ref}
      className="relative py-28 lg:py-36 border-b border-white/[0.06] bg-[#080B10] overflow-hidden"
    >
      {/* Massive Outlined Background Chapter Number */}
      <BackgroundChapterNo number="03" className="top-12 right-6 lg:right-16" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="max-w-2xl mb-16 sm:mb-20 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">
            <span className="text-slate-500">Chapter 03</span>
            <span className="text-slate-600">/</span>
            <span className="text-violet-400 font-medium font-sans">The Unified Platform</span>
          </div>

          <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl text-white font-normal leading-[1.12]">
            <SplitTextReveal
              text="Four interconnected hubs. One neural intelligence core."
              delayOffsetMs={100}
              charDelayMs={18}
              isRevealed={isRevealed}
            />
          </h2>

          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            In Opportunity OS, information does not sit in static tables. Autonomous agent shuttles traverse optical conduits connecting all collegiate participants.
          </p>
        </div>

        {/* 4 Conduits Architectural Grid with Staggered Cascading Delays */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {CONDUITS.map((c, idx) => {
            const Icon = c.icon;
            return (
              <ScrollRevealCard key={c.title} delayMs={idx * 120}>
                <div
                  className={`rounded-2xl border ${c.border} ${c.bg} p-6 space-y-4 card-hover-lift h-full`}
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-2.5 rounded-xl bg-white/[0.05] ${c.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      {c.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-white">{c.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{c.desc}</p>
                </div>
              </ScrollRevealCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
