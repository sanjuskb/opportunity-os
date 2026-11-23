'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { Menu, X, Globe, ChevronDown, ArrowUpRight } from 'lucide-react';

export function LandingNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedLang, setSelectedLang] = useState<string>(APP_CONFIG.DEFAULT_LANGUAGE);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [activeChapter, setActiveChapter] = useState<'01' | '02' | '03' | '04' | '05' | '06' | '07'>('01');

  const activeLangObj = APP_CONFIG.SUPPORTED_LANGUAGES.find((l) => l.code === selectedLang);

  const CHAPTER_TITLES: Record<string, string> = {
    '01': 'The Ecosystem',
    '02': 'The Fragmentation',
    '03': 'Unified Platform',
    '04': 'For Students',
    '05': 'For Companies',
    '06': 'For Universities',
    '07': 'Voice Intelligence',
  };

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = scrollY / (docHeight || 1);

      if (progress < 0.15) setActiveChapter('01');
      else if (progress < 0.3) setActiveChapter('02');
      else if (progress < 0.45) setActiveChapter('03');
      else if (progress < 0.6) setActiveChapter('04');
      else if (progress < 0.75) setActiveChapter('05');
      else if (progress < 0.9) setActiveChapter('06');
      else setActiveChapter('07');
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-white/[0.07] bg-[#080B10]/80 backdrop-blur-xl transition-all duration-300">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Identity */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-950/60 border border-indigo-500/30 shadow-[0_0_15px_rgba(139,92,246,0.2)] transition group-hover:border-cyan-400/60">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <div className="absolute inset-0 rounded-lg ring-1 ring-inset ring-white/10" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-white group-hover:text-cyan-300 transition">
                Opportunity <span className="text-cyan-400">OS</span>
              </span>
              <span className="text-[10px] font-mono text-slate-500 tracking-wider">Homingo Ed. 01</span>
            </div>
          </Link>

          {/* Persistent Chapter Index Tracker (Homingo-inspired Spatial Indicator) */}
          <div className="hidden lg:flex items-center gap-2.5 pl-6 border-l border-white/[0.08] text-xs font-mono">
            <span className="text-cyan-400 font-semibold">{activeChapter}</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-500">07</span>
            <span className="text-slate-400 font-sans tracking-normal font-medium text-xs ml-1">
              — {CHAPTER_TITLES[activeChapter]}
            </span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-xs font-medium text-slate-300 tracking-wide">
          <a href="#ecosystem" className="hover:text-white transition-colors duration-200">
            Ecosystem
          </a>
          <a href="#students" className="hover:text-cyan-300 transition-colors duration-200">
            Students
          </a>
          <a href="#companies" className="hover:text-blue-300 transition-colors duration-200">
            Companies
          </a>
          <a href="#universities" className="hover:text-emerald-300 transition-colors duration-200">
            Universities
          </a>
          <a href="#voice-ai" className="hover:text-violet-300 transition-colors duration-200">
            Voice AI
          </a>
        </nav>

        {/* Right Controls: Language Selector + Sign In + Primary Action */}
        <div className="hidden md:flex items-center gap-4">
          <Link
            href="/login"
            className="text-xs font-medium text-slate-300 hover:text-white px-2 py-1 transition-colors"
          >
            Sign In
          </Link>

          {/* Indic Language Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
              className="flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-[#0F141E] px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:border-white/20 hover:text-white transition"
              aria-label="Select language"
              aria-expanded={langDropdownOpen}
            >
              <Globe className="h-3.5 w-3.5 text-cyan-400" />
              <span>{activeLangObj?.name ?? 'English'}</span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {langDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-xl border border-white/10 bg-[#0F141E] p-1.5 shadow-2xl backdrop-blur-2xl ring-1 ring-black/60 z-50">
                <div className="px-2.5 py-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  Native Indic Languages
                </div>
                {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setSelectedLang(lang.code);
                      setLangDropdownOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs transition ${
                      selectedLang === lang.code
                        ? 'bg-cyan-500/15 text-cyan-300 font-semibold'
                        : 'text-slate-300 hover:bg-white/[0.06] hover:text-white'
                    }`}
                  >
                    <span>{lang.name}</span>
                    <span className="text-[11px] text-slate-500 font-mono">{lang.native}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Launch OS Button */}
          <Link
            href="/overview"
            className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.08] hover:bg-white/[0.14] border border-white/10 px-4 py-1.5 text-xs font-medium text-white shadow-sm transition group"
          >
            <span>Launch OS</span>
            <ArrowUpRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-cyan-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition" />
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-white focus:outline-none"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-white/10 bg-[#080B10] px-4 pt-3 pb-6 space-y-3">
          <a
            href="#ecosystem"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.06]"
          >
            01 — The Ecosystem
          </a>
          <a
            href="#students"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.06]"
          >
            04 — For Students
          </a>
          <a
            href="#companies"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.06]"
          >
            05 — For Companies
          </a>
          <a
            href="#universities"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.06]"
          >
            06 — For Universities
          </a>
          <a
            href="#voice-ai"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.06]"
          >
            07 — Voice Intelligence
          </a>
          <div className="pt-3 border-t border-white/10 flex items-center justify-between">
            <Link
              href="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="text-xs text-slate-400 hover:text-white font-medium"
            >
              Sign In
            </Link>
            <Link
              href="/overview"
              onClick={() => setMobileMenuOpen(false)}
              className="inline-flex items-center gap-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-3 py-1.5 text-xs font-semibold"
            >
              Launch OS <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
