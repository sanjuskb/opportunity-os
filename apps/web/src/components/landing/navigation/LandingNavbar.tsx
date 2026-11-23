'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { Menu, X, Globe, Sparkles, ChevronDown } from 'lucide-react';

export function LandingNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedLang, setSelectedLang] = useState<string>(APP_CONFIG.DEFAULT_LANGUAGE);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  const activeLangObj = APP_CONFIG.SUPPORTED_LANGUAGES.find((l) => l.code === selectedLang);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-[#090D16]/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand / Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600/20 border border-indigo-500/40 shadow-[0_0_15px_rgba(99,102,241,0.25)] transition group-hover:border-indigo-400">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <div className="absolute inset-0 rounded-lg ring-1 ring-inset ring-indigo-400/20" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white group-hover:text-cyan-300 transition">
            Opportunity <span className="text-cyan-400">OS</span>
          </span>
          <span className="hidden sm:inline-flex items-center rounded-full bg-indigo-950/60 px-2 py-0.5 text-[10px] font-medium text-indigo-300 border border-indigo-800/40">
            v0.1
          </span>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-300">
          <Link href="/opportunities" className="hover:text-white transition">
            Opportunities
          </Link>
          <Link href="/career-passport" className="hover:text-white transition">
            Career Passport
          </Link>
          <a href="#ecosystem-campus" className="hover:text-white transition flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Campus Ecosystem
          </a>
          <a href="#voice-ai" className="hover:text-white transition flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-violet-400" />
            Voice Intelligence
          </a>
        </nav>

        {/* Right Section: Language Selector + CTA */}
        <div className="hidden md:flex items-center gap-3.5">
          {/* Language Selector Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700 hover:text-white transition"
              aria-label="Select language"
              aria-expanded={langDropdownOpen}
            >
              <Globe className="h-3.5 w-3.5 text-cyan-400" />
              <span>{activeLangObj?.name ?? 'English'}</span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {langDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-lg border border-slate-800 bg-[#0F172A] p-1.5 shadow-xl ring-1 ring-black/40 z-50">
                <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Supported Languages
                </div>
                {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setSelectedLang(lang.code);
                      setLangDropdownOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-xs transition ${
                      selectedLang === lang.code
                        ? 'bg-indigo-600/20 text-cyan-300 font-semibold'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <span>{lang.name}</span>
                    <span className="text-[11px] text-slate-400">{lang.native}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Primary Action Button */}
          <Link
            href="/opportunities"
            className="inline-flex items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-500 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:from-indigo-500 hover:to-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 transition"
          >
            Launch OS
          </Link>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="inline-flex items-center justify-center rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white focus:outline-none"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Panel */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-[#090D16] px-4 pt-2 pb-4 space-y-2">
          <Link
            href="/opportunities"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-md px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            Opportunities
          </Link>
          <Link
            href="/career-passport"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-md px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            Career Passport
          </Link>
          <a
            href="#ecosystem-campus"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-md px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            Campus Ecosystem
          </a>
          <a
            href="#voice-ai"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-md px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            Voice Intelligence
          </a>
          <div className="pt-2 border-t border-slate-800/80">
            <Link
              href="/opportunities"
              onClick={() => setMobileMenuOpen(false)}
              className="flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500"
            >
              Launch OS
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
