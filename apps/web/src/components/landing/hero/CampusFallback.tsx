'use client';

import React from 'react';
import type { EcosystemRole } from './RoleSwitcher';
import { Sparkles } from 'lucide-react';

interface CampusFallbackProps {
  activeHub?: EcosystemRole | 'core';
  onSelectHub?: (hub: EcosystemRole) => void;
}

export function CampusFallback({
  activeHub = 'students',
  onSelectHub,
}: CampusFallbackProps) {
  return (
    <div
      className="relative w-full h-[450px] sm:h-[520px] lg:h-[600px] rounded-2xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-2xl flex flex-col items-center justify-center p-4 select-none"
      aria-label="Interactive Ecosystem Campus Architecture Maquette"
    >
      {/* Background Architectural Grid Pattern */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 70%), linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(90deg, #1e293b 1px, transparent 1px)',
          backgroundSize: '100% 100%, 32px 32px, 32px 32px',
        }}
      />

      {/* SVG Isometric Maquette Diagram */}
      <svg
        viewBox="0 0 600 500"
        className="w-full h-full max-w-lg z-10"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Gradients */}
          <radialGradient id="aiCorePulse" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#C084FC" stopOpacity="0.9" />
            <stop offset="60%" stopColor="#8B5CF6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#4F46E5" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="pathCyan" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="pathBlue" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="pathGreen" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="pathAmber" x1="100%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
          </linearGradient>

          {/* Glow filter */}
          <filter id="glowFilter" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Baseplate Obsidian Polygon */}
        <polygon
          points="300,70 540,210 300,380 60,210"
          fill="#0d1322"
          stroke="#1e293b"
          strokeWidth="2"
        />
        <polygon
          points="300,380 540,210 540,230 300,400 60,230 60,210"
          fill="#070b14"
          stroke="#111827"
          strokeWidth="1"
        />

        {/* Optical Channels (Pathways connecting hubs to center) */}
        {/* Top/North to Center: Universities */}
        <line
          x1="300"
          y1="125"
          x2="300"
          y2="215"
          stroke="url(#pathGreen)"
          strokeWidth="4"
          strokeDasharray="6 4"
        />
        {/* Right/East to Center: Companies */}
        <line
          x1="460"
          y1="210"
          x2="330"
          y2="225"
          stroke="url(#pathBlue)"
          strokeWidth="4"
          strokeDasharray="6 4"
        />
        {/* Bottom/South to Center: Opportunities */}
        <line
          x1="300"
          y1="320"
          x2="300"
          y2="235"
          stroke="url(#pathAmber)"
          strokeWidth="4"
          strokeDasharray="6 4"
        />
        {/* Left/West to Center: Students */}
        <line
          x1="140"
          y1="210"
          x2="270"
          y2="225"
          stroke="url(#pathCyan)"
          strokeWidth="4"
          strokeDasharray="6 4"
        />

        {/* Moving Agent Shuttle Indicators */}
        <circle cx="215" cy="218" r="3.5" fill="#38BDF8" filter="url(#glowFilter)">
          <animate attributeName="cx" values="150;265;150" dur="4s" repeatCount="indefinite" />
        </circle>
        <circle cx="300" cy="170" r="3.5" fill="#34D399" filter="url(#glowFilter)">
          <animate attributeName="cy" values="135;210;135" dur="3.5s" repeatCount="indefinite" />
        </circle>
        <circle cx="395" cy="218" r="3.5" fill="#60A5FA" filter="url(#glowFilter)">
          <animate attributeName="cx" values="450;335;450" dur="4.2s" repeatCount="indefinite" />
        </circle>
        <circle cx="300" cy="280" r="3.5" fill="#FBBF24" filter="url(#glowFilter)">
          <animate attributeName="cy" values="310;240;310" dur="3.8s" repeatCount="indefinite" />
        </circle>

        {/* Central AI Intelligence Core */}
        <g transform="translate(300, 225)">
          <ellipse rx="45" ry="25" fill="#4338CA" opacity="0.3" filter="url(#glowFilter)" />
          <circle r="22" fill="url(#aiCorePulse)" filter="url(#glowFilter)" />
          <circle r="14" fill="#090D16" stroke="#A855F7" strokeWidth="2" />
          <circle r="5" fill="#C084FC">
            <animate attributeName="r" values="4;7;4" dur="2s" repeatCount="indefinite" />
          </circle>
          <text
            y="35"
            textAnchor="middle"
            fill="#E2E8F0"
            fontSize="10"
            fontWeight="bold"
            letterSpacing="0.5"
          >
            AI CORE
          </text>
        </g>

        {/* Hub 1: Students (West / Left) */}
        <g
          transform="translate(140, 210)"
          className="cursor-pointer"
          onClick={() => onSelectHub?.('students')}
        >
          <polygon
            points="0,-25 25,-10 25,15 0,30 -25,15 -25,-10"
            fill="#082F49"
            stroke={activeHub === 'students' ? '#38BDF8' : '#0284C7'}
            strokeWidth={activeHub === 'students' ? '3' : '1.5'}
            filter={activeHub === 'students' ? 'url(#glowFilter)' : undefined}
          />
          <circle r="6" fill="#06B6D4" />
          <text
            y="42"
            textAnchor="middle"
            fill="#E0F2FE"
            fontSize="10"
            fontWeight="600"
          >
            Students
          </text>
        </g>

        {/* Hub 2: Companies (East / Right) */}
        <g
          transform="translate(460, 210)"
          className="cursor-pointer"
          onClick={() => onSelectHub?.('companies')}
        >
          <polygon
            points="0,-25 25,-10 25,15 0,30 -25,15 -25,-10"
            fill="#172554"
            stroke={activeHub === 'companies' ? '#60A5FA' : '#2563EB'}
            strokeWidth={activeHub === 'companies' ? '3' : '1.5'}
            filter={activeHub === 'companies' ? 'url(#glowFilter)' : undefined}
          />
          <circle r="6" fill="#3B82F6" />
          <text
            y="42"
            textAnchor="middle"
            fill="#EFF6FF"
            fontSize="10"
            fontWeight="600"
          >
            Companies
          </text>
        </g>

        {/* Hub 3: Universities (North / Top) */}
        <g
          transform="translate(300, 125)"
          className="cursor-pointer"
          onClick={() => onSelectHub?.('universities')}
        >
          <polygon
            points="0,-25 25,-10 25,15 0,30 -25,15 -25,-10"
            fill="#064E3B"
            stroke={activeHub === 'universities' ? '#34D399' : '#059669'}
            strokeWidth={activeHub === 'universities' ? '3' : '1.5'}
            filter={activeHub === 'universities' ? 'url(#glowFilter)' : undefined}
          />
          <circle r="6" fill="#10B981" />
          <text
            y="-32"
            textAnchor="middle"
            fill="#ECFDF5"
            fontSize="10"
            fontWeight="600"
          >
            Universities
          </text>
        </g>

        {/* Hub 4: Opportunities (South / Bottom) */}
        <g
          transform="translate(300, 320)"
          className="cursor-pointer"
          onClick={() => onSelectHub?.('opportunities')}
        >
          <polygon
            points="0,-25 25,-10 25,15 0,30 -25,15 -25,-10"
            fill="#451A03"
            stroke={activeHub === 'opportunities' ? '#FBBF24' : '#D97706'}
            strokeWidth={activeHub === 'opportunities' ? '3' : '1.5'}
            filter={activeHub === 'opportunities' ? 'url(#glowFilter)' : undefined}
          />
          <circle r="6" fill="#F59E0B" />
          <text
            y="44"
            textAnchor="middle"
            fill="#FEF3C7"
            fontSize="10"
            fontWeight="600"
          >
            Opportunities
          </text>
        </g>
      </svg>

      {/* Floating Status Badge */}
      <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-xs text-slate-400 bg-slate-950/70 border border-slate-800/80 px-3 py-1.5 rounded-lg backdrop-blur-sm z-20">
        <span className="flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>Interactive Architectural Maquette</span>
        </span>
        <span className="text-[10px] text-slate-500 font-mono">
          Concept 4 + Concept 1
        </span>
      </div>
    </div>
  );
}
