'use client';

import React from 'react';

interface SpatialBackgroundProps {
  variant: 'fragmented' | 'transit' | 'journey' | 'pipeline' | 'institutional' | 'harmonic';
  className?: string;
}

export function SpatialBackground({ variant, className = '' }: SpatialBackgroundProps) {
  return (
    <div
      className={`absolute inset-0 pointer-events-none overflow-hidden select-none ${className}`}
      aria-hidden="true"
    >
      {variant === 'fragmented' && (
        <div className="absolute inset-0 flex items-center justify-end pr-8 sm:pr-16 opacity-30">
          <svg
            className="w-[380px] h-[380px] sm:w-[480px] sm:h-[480px] text-amber-500/20"
            viewBox="0 0 400 400"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Disconnected floating isometric architectural blocks */}
            <g className="animate-ambient-float" style={{ animationDuration: '9s' }}>
              <polygon points="120,60 180,30 240,60 180,90" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.03)" />
              <polygon points="120,60 120,110 180,140 180,90" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.05)" />
              <polygon points="240,60 240,110 180,140 180,90" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.08)" />
            </g>

            <g className="animate-ambient-float" style={{ animationDuration: '11s', animationDelay: '-3s' }}>
              <polygon points="260,180 320,150 380,180 320,210" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.03)" />
              <polygon points="260,180 260,230 320,260 320,210" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.05)" />
              <polygon points="380,180 380,230 320,260 320,210" stroke="currentColor" strokeWidth="1" fill="rgba(245, 158, 11, 0.08)" />
            </g>

            {/* Fractured conduit lines */}
            <path d="M180,140 L220,170 M240,185 L260,200" stroke="rgba(239, 68, 68, 0.4)" strokeWidth="1.5" strokeDasharray="4 4" />
            <path d="M120,110 L80,140" stroke="rgba(245, 158, 11, 0.3)" strokeWidth="1" strokeDasharray="2 3" />
          </svg>
        </div>
      )}

      {variant === 'transit' && (
        <div className="absolute inset-0 flex items-center justify-end pr-6 sm:pr-20 opacity-25">
          <svg
            className="w-[420px] h-[420px] sm:w-[540px] sm:h-[540px] text-violet-500/25"
            viewBox="0 0 500 500"
            fill="none"
          >
            {/* Concentric orbital rings */}
            <circle cx="250" cy="250" r="180" stroke="currentColor" strokeWidth="1" strokeDasharray="6 8" />
            <circle cx="250" cy="250" r="120" stroke="rgba(6, 182, 212, 0.3)" strokeWidth="1" />
            <circle cx="250" cy="250" r="60" stroke="rgba(139, 92, 246, 0.5)" strokeWidth="1.5" />
            <circle cx="250" cy="250" r="14" fill="rgba(139, 92, 246, 0.3)" stroke="rgba(139, 92, 246, 0.8)" />

            {/* Orbital node satellites */}
            <circle cx="430" cy="250" r="4" fill="#06B6D4" />
            <circle cx="160" cy="146" r="4" fill="#3B82F6" />
            <circle cx="340" cy="354" r="4" fill="#10B981" />
            <circle cx="190" cy="354" r="4" fill="#F59E0B" />
          </svg>
        </div>
      )}

      {variant === 'journey' && (
        <div className="absolute inset-0 flex items-center justify-end pr-10 opacity-20">
          <svg className="w-[440px] h-[440px] text-cyan-400/30" viewBox="0 0 400 400" fill="none">
            {/* Layered ascending architectural prisms */}
            <g className="animate-ambient-float" style={{ animationDuration: '8s' }}>
              <polygon points="100,280 200,230 300,280 200,330" stroke="currentColor" strokeWidth="1" fill="rgba(6, 182, 212, 0.04)" />
              <polygon points="120,230 200,190 280,230 200,270" stroke="currentColor" strokeWidth="1" fill="rgba(6, 182, 212, 0.06)" />
              <polygon points="140,180 200,150 260,180 200,210" stroke="currentColor" strokeWidth="1" fill="rgba(6, 182, 212, 0.08)" />
              <polygon points="160,130 200,110 240,130 200,150" stroke="currentColor" strokeWidth="1.5" fill="rgba(6, 182, 212, 0.12)" />
            </g>
            <line x1="200" y1="110" x2="200" y2="40" stroke="rgba(6, 182, 212, 0.5)" strokeWidth="1.5" strokeDasharray="3 3" />
            <circle cx="200" cy="35" r="4" fill="#06B6D4" />
          </svg>
        </div>
      )}

      {variant === 'pipeline' && (
        <div className="absolute inset-0 flex items-center justify-start pl-8 opacity-20">
          <svg className="w-[440px] h-[440px] text-blue-500/30" viewBox="0 0 400 400" fill="none">
            {/* Isometric recruitment matrix grid */}
            <path
              d="M50,150 L200,75 L350,150 L200,225 Z M50,225 L200,150 L350,225 L200,300 Z"
              stroke="currentColor"
              strokeWidth="1"
              fill="rgba(59, 130, 246, 0.03)"
            />
            <circle cx="200" cy="150" r="5" fill="#3B82F6" />
            <circle cx="125" cy="187" r="3.5" fill="#3B82F6" />
            <circle cx="275" cy="187" r="3.5" fill="#3B82F6" />
            <line x1="200" y1="75" x2="200" y2="300" stroke="rgba(59, 130, 246, 0.3)" strokeWidth="1" strokeDasharray="4 4" />
          </svg>
        </div>
      )}

      {variant === 'institutional' && (
        <div className="absolute inset-0 flex items-center justify-end pr-12 opacity-20">
          <svg className="w-[420px] h-[420px] text-emerald-500/30" viewBox="0 0 400 400" fill="none">
            {/* Stepped architectural institutional crest */}
            <rect x="140" y="80" width="120" height="120" rx="8" stroke="currentColor" strokeWidth="1" transform="rotate(45 200 140)" fill="rgba(16, 185, 129, 0.04)" />
            <rect x="160" y="100" width="80" height="80" rx="6" stroke="currentColor" strokeWidth="1" transform="rotate(45 200 140)" fill="rgba(16, 185, 129, 0.06)" />
            <circle cx="200" cy="140" r="10" stroke="currentColor" strokeWidth="1.5" />
            <line x1="200" y1="230" x2="200" y2="320" stroke="rgba(16, 185, 129, 0.3)" strokeWidth="1" strokeDasharray="3 3" />
          </svg>
        </div>
      )}

      {variant === 'harmonic' && (
        <div className="absolute inset-0 flex items-center justify-end pr-10 opacity-25">
          <svg className="w-[460px] h-[460px] text-violet-500/30" viewBox="0 0 400 400" fill="none">
            {/* Concentric undulating harmonic rings */}
            <circle cx="200" cy="200" r="160" stroke="currentColor" strokeWidth="0.75" strokeDasharray="4 8" />
            <circle cx="200" cy="200" r="120" stroke="currentColor" strokeWidth="1" strokeDasharray="6 6" />
            <circle cx="200" cy="200" r="80" stroke="currentColor" strokeWidth="1.25" />
            <circle cx="200" cy="200" r="40" stroke="rgba(168, 85, 247, 0.7)" strokeWidth="1.5" />
          </svg>
        </div>
      )}
    </div>
  );
}
