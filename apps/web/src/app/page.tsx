import React from 'react';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-3xl space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <span>Homingo Hackathon Edition 01</span>
          <span>•</span>
          <span>Voice-First AI Platform</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-cyan-400 to-sky-300 bg-clip-text text-transparent">
          {APP_CONFIG.APP_NAME}
        </h1>

        <p className="text-lg md:text-xl text-slate-400 leading-relaxed">
          AI-powered career &amp; internship intelligence platform for Indian students.
          Explore opportunities, verify eligibility, craft ATS resumes, and execute workflows in 7 native languages.
        </p>

        <div className="flex flex-wrap justify-center gap-2 pt-2">
          {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
            <span
              key={lang.code}
              className="px-2.5 py-1 text-xs rounded-md bg-slate-800/80 border border-slate-700 text-slate-300"
            >
              {lang.native} ({lang.name})
            </span>
          ))}
        </div>

        <div className="pt-4 flex items-center justify-center gap-4">
          <a
            href="/opportunities"
            className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition"
          >
            Explore Opportunities
          </a>
          <a
            href="/career-passport"
            className="px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium border border-slate-700 transition"
          >
            Career Passport
          </a>
        </div>
      </div>
    </main>
  );
}
