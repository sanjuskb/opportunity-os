import React from 'react';
import Link from 'next/link';
import { LandingNavbar } from '../../components/landing/navigation/LandingNavbar';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Mic, Volume2, Globe, Radio, ArrowRight } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export default function VoiceAiPage() {
  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col">
      <LandingNavbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <Badge variant="violet">14-State Acoustic Engine</Badge>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white">Indic Voice Intelligence</h1>
          <p className="text-base text-slate-300">
            Breaking the linguistic barrier. Speak your mother tongue to explore verified opportunities and practice technical interviews.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => (
            <div key={l.code} className="rounded-xl border border-slate-800 bg-[#0D1322] p-5 space-y-2">
              <div className="flex items-center justify-between">
                <Volume2 className="h-5 w-5 text-violet-400" />
                <span className="font-mono text-xs text-slate-400 uppercase">{l.code}</span>
              </div>
              <div className="text-base font-bold text-white">{l.name}</div>
              <div className="text-xs text-slate-400 font-medium">{l.native}</div>
            </div>
          ))}
        </div>

        <div className="p-8 rounded-2xl border border-violet-500/30 bg-gradient-to-r from-violet-950/30 to-[#0B0F19] text-center space-y-4">
          <h2 className="text-xl font-bold text-white">Experience Real-Time Voice Search</h2>
          <p className="text-xs text-slate-300 max-w-md mx-auto">
            Test the live microphone audio stream and interactive translation inside the student workspace.
          </p>
          <Link href="/overview">
            <Button variant="glow" size="md">
              <Mic className="h-4 w-4 mr-2" />
              <span>Launch Voice Demo in Workspace</span>
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
