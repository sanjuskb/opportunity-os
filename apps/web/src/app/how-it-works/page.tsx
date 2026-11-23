import React from 'react';
import Link from 'next/link';
import { LandingNavbar } from '../../components/landing/navigation/LandingNavbar';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Compass, Sparkles, ShieldCheck, Send, ArrowRight } from 'lucide-react';

export default function HowItWorksPage() {
  const steps = [
    {
      num: '01',
      title: 'Autonomous Ingestion',
      icon: Compass,
      desc: 'Our distributed scrapers (Olostep & Crustdata) continuously ingest 10,000+ internships, research fellowships, and government grants across India.',
      color: 'text-amber-400',
    },
    {
      num: '02',
      title: 'Deterministic Eligibility Matching',
      icon: Sparkles,
      desc: 'Our algorithmic matching engine executes strict pre-checks on graduation year, degree, and CGPA, calculating a transparent composite match score.',
      color: 'text-cyan-400',
    },
    {
      num: '03',
      title: 'Institutional Verification (Career Passport)',
      icon: ShieldCheck,
      desc: 'Your college coursework, NPTEL scores, and verified GitHub commits are bound into a cryptographic Career Passport accredited via AICTE DigiLocker.',
      color: 'text-emerald-400',
    },
    {
      num: '04',
      title: 'Agentic Tailoring & Approval Dispatch',
      icon: Send,
      desc: 'AI agent shuttles craft targeted ATS bullet points tailored to the employer rubric. With your one-click approval, the verified application is dispatched.',
      color: 'text-violet-400',
    },
  ];

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col">
      <LandingNavbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <Badge variant="cyan">4-Step Lifecycle</Badge>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white">How Opportunity OS Works</h1>
          <p className="text-base text-slate-300">
            From raw opportunity discovery to verified submission in minutes, without ever fabricating credentials.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {steps.map((st) => {
            const Icon = st.icon;
            return (
              <div key={st.num} className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-3 relative">
                <div className="flex items-center justify-between">
                  <div className={`p-3 rounded-xl bg-slate-900 border border-slate-800 ${st.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <span className="font-mono text-3xl font-black text-slate-700">{st.num}</span>
                </div>
                <h2 className="text-lg font-bold text-white">{st.title}</h2>
                <p className="text-xs text-slate-300 leading-relaxed">{st.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="text-center pt-8">
          <Link href="/opportunities">
            <Button variant="glow" size="lg">
              <span>Explore Verified Opportunities</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        Opportunity OS • Autonomous Intelligence Campus • Apache-2.0
      </footer>
    </div>
  );
}
