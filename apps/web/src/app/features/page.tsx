import React from 'react';
import Link from 'next/link';
import { LandingNavbar } from '../../components/landing/navigation/LandingNavbar';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Mic, Award, FileText, Bot, ShieldCheck, Compass, ArrowRight } from 'lucide-react';

export default function FeaturesPage() {
  const features = [
    {
      title: '7-Language Voice Copilot',
      icon: Mic,
      desc: 'Speak naturally in Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, or English to explore opportunities and practice technical interviews.',
      badge: 'Indic NLP',
    },
    {
      title: 'Verified Career Passport',
      icon: Award,
      desc: 'A digital, tamper-proof academic identity linked to AICTE DigiLocker, NPTEL certificates, and verified GitHub commits.',
      badge: 'Zero Hallucinations',
    },
    {
      title: 'ATS Resume Studio',
      icon: FileText,
      desc: 'Instant 94% parseable ATS scoring with AI-optimized bullet points quantified to highlight impact, latency, and throughput.',
      badge: 'Scored 94/100',
    },
    {
      title: 'Autonomous Agent Shuttles',
      icon: Bot,
      desc: 'Proactive background agents that crawl job portals, match criteria, and prepare application drafts without prompt fatigue.',
      badge: 'Proactive AI',
    },
    {
      title: 'Explainable Eligibility Pre-checks',
      icon: ShieldCheck,
      desc: 'Never waste time on dead-end applications. Instantly view batch match, degree match, and exact skill gaps before applying.',
      badge: 'Transparent Rubric',
    },
    {
      title: 'Live Indic Ingestion Pipeline',
      icon: Compass,
      desc: 'Aggregating from Olostep, Crustdata, research institutes, and corporate job boards into one structured intelligence stream.',
      badge: '10k+ Postings',
    },
  ];

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col">
      <LandingNavbar />

      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <Badge variant="cyan">Platform Capabilities</Badge>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white">The NexteRaS Feature Suite</h1>
          <p className="text-base text-slate-300">
            A comprehensive operating system designed specifically for the Indian collegiate ecosystem.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400">
                    <Icon className="h-6 w-6" />
                  </div>
                  <Badge variant="slate">{f.badge}</Badge>
                </div>
                <h2 className="text-base font-bold text-white">{f.title}</h2>
                <p className="text-xs text-slate-300 leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="text-center pt-8">
          <Link href="/register">
            <Button variant="glow" size="lg">
              <span>Get Started Now</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        NexteRaS • AI Career Intelligence &amp; Autonomous Employability System • Apache-2.0
      </footer>
    </div>
  );
}
