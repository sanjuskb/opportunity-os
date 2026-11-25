import React from 'react';
import Link from 'next/link';
import { LandingNavbar } from '../../components/landing/navigation/LandingNavbar';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Bot, ShieldCheck, Zap, Lock, Cpu, ArrowRight } from 'lucide-react';

export default function AiAgentsPage() {
  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col">
      <LandingNavbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <Badge variant="sapphire">Autonomous Agent Architecture</Badge>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white">Autonomous Agent Shuttles</h1>
          <p className="text-base text-slate-300">
            Intelligent background workers moving data and executing workflows with deterministic safety guardrails.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-4">
            <div className="p-3 rounded-xl bg-blue-950/60 border border-blue-500/30 text-blue-400 w-fit">
              <Bot className="h-6 w-6" />
            </div>
            <h2 className="text-lg font-bold text-white">How Shuttles Operate</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              In our 3D Neural Transit Atlas, agent shuttles physically travel along optical pathways between the four hubs. In the software stack, these correspond to LangGraph orchestrated agents performing continuous ingestion, ATS calculation, and candidate dispatch.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 space-y-4">
            <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 w-fit">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h2 className="text-lg font-bold text-white">Human-in-the-Loop Guardrail</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              NexteRaS strictly enforces a zero-unauthorized-action policy. Shuttles prepare tailored application packages, but they never submit an application or send an outreach email without explicit student review and one-click cryptographic approval.
            </p>
          </div>
        </div>

        <div className="text-center pt-8">
          <Link href="/overview">
            <Button variant="glow" size="lg">
              <span>View Live Agent Telemetry</span>
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
