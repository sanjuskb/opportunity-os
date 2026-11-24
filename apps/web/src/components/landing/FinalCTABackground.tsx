'use client';

import React from 'react';

/**
 * High-end retrofuturistic background featuring:
 * - 3D Perspective Cyber Horizon Grid
 * - Liquid Glass Aurora Glows (Cyan & Violet caustics)
 * - Drifting Luminous Neural Particles
 * - Concentric Quantum Horizon Ripples
 */
export function FinalCTABackground() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
      {/* 1. Liquid Glass Aurora Fields */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[550px] bg-gradient-to-tr from-cyan-600/15 via-violet-600/20 to-indigo-600/10 blur-[160px] rounded-full" />
      <div className="absolute top-1/3 left-1/4 w-[450px] h-[350px] bg-cyan-400/10 blur-[130px] rounded-full animate-ambient-float" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[400px] bg-violet-500/15 blur-[140px] rounded-full" />

      {/* 2. Concentric Quantum Horizon Ellipses */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[500px] rounded-[100%] border border-cyan-500/[0.12] opacity-60" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1150px] h-[680px] rounded-[100%] border border-violet-500/[0.08] opacity-50" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1450px] h-[860px] rounded-[100%] border border-white/[0.04] opacity-40" />

      {/* 3. Retrofuturistic 3D Perspective Horizon Grid (SVG) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-35"
        preserveAspectRatio="none"
        viewBox="0 0 1440 900"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="horizonVanish" x1="0%" y1="50%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.4" />
            <stop offset="40%" stopColor="#8B5CF6" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#080B10" stopOpacity="0" />
          </linearGradient>

          <linearGradient id="horizonVanishTop" x1="0%" y1="50%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.3" />
            <stop offset="50%" stopColor="#06B6D4" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#080B10" stopOpacity="0" />
          </linearGradient>

          <radialGradient id="centerBurst" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.6" />
            <stop offset="30%" stopColor="#8B5CF6" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#080B10" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Central Horizon Glow Line */}
        <line x1="0" y1="450" x2="1440" y2="450" stroke="url(#centerBurst)" strokeWidth="1.5" />

        {/* Lower Perspective Floor Grid */}
        <g stroke="url(#horizonVanish)" strokeWidth="0.8">
          {/* Vanishing converging perspective rays */}
          <line x1="720" y1="450" x2="-200" y2="950" />
          <line x1="720" y1="450" x2="60" y2="950" />
          <line x1="720" y1="450" x2="280" y2="950" />
          <line x1="720" y1="450" x2="500" y2="950" />
          <line x1="720" y1="450" x2="640" y2="950" />
          <line x1="720" y1="450" x2="720" y2="950" />
          <line x1="720" y1="450" x2="800" y2="950" />
          <line x1="720" y1="450" x2="940" y2="950" />
          <line x1="720" y1="450" x2="1160" y2="950" />
          <line x1="720" y1="450" x2="1380" y2="950" />
          <line x1="720" y1="450" x2="1640" y2="950" />

          {/* Exponentially spaced horizontal perspective crossbars */}
          <line x1="0" y1="455" x2="1440" y2="455" strokeOpacity="0.8" />
          <line x1="0" y1="465" x2="1440" y2="465" strokeOpacity="0.75" />
          <line x1="0" y1="480" x2="1440" y2="480" strokeOpacity="0.7" />
          <line x1="0" y1="505" x2="1440" y2="505" strokeOpacity="0.6" />
          <line x1="0" y1="545" x2="1440" y2="545" strokeOpacity="0.5" />
          <line x1="0" y1="605" x2="1440" y2="605" strokeOpacity="0.4" />
          <line x1="0" y1="690" x2="1440" y2="690" strokeOpacity="0.3" />
          <line x1="0" y1="810" x2="1440" y2="810" strokeOpacity="0.2" />
        </g>

        {/* Upper Perspective Ceiling Grid */}
        <g stroke="url(#horizonVanishTop)" strokeWidth="0.6">
          <line x1="720" y1="450" x2="-200" y2="-50" />
          <line x1="720" y1="450" x2="100" y2="-50" />
          <line x1="720" y1="450" x2="380" y2="-50" />
          <line x1="720" y1="450" x2="620" y2="-50" />
          <line x1="720" y1="450" x2="720" y2="-50" />
          <line x1="720" y1="450" x2="820" y2="-50" />
          <line x1="720" y1="450" x2="1060" y2="-50" />
          <line x1="720" y1="450" x2="1340" y2="-50" />
          <line x1="720" y1="450" x2="1640" y2="-50" />

          {/* Exponentially spaced horizontal ceiling crossbars */}
          <line x1="0" y1="445" x2="1440" y2="445" strokeOpacity="0.7" />
          <line x1="0" y1="435" x2="1440" y2="435" strokeOpacity="0.65" />
          <line x1="0" y1="418" x2="1440" y2="418" strokeOpacity="0.55" />
          <line x1="0" y1="390" x2="1440" y2="390" strokeOpacity="0.45" />
          <line x1="0" y1="345" x2="1440" y2="345" strokeOpacity="0.35" />
          <line x1="0" y1="280" x2="1440" y2="280" strokeOpacity="0.25" />
          <line x1="0" y1="180" x2="1440" y2="180" strokeOpacity="0.15" />
        </g>
      </svg>

      {/* 4. Drifting Luminous Particles & Constellation Nodes */}
      <div className="absolute inset-0">
        {[
          { top: '22%', left: '18%', size: 3, delay: '0s', color: 'bg-cyan-300' },
          { top: '35%', left: '82%', size: 4, delay: '1.2s', color: 'bg-violet-300' },
          { top: '65%', left: '25%', size: 3.5, delay: '2.4s', color: 'bg-sky-400' },
          { top: '75%', left: '78%', size: 2.5, delay: '0.8s', color: 'bg-cyan-400' },
          { top: '15%', left: '60%', size: 3, delay: '3.1s', color: 'bg-indigo-300' },
          { top: '82%', left: '42%', size: 4, delay: '1.9s', color: 'bg-violet-400' },
          { top: '28%', left: '38%', size: 2.5, delay: '2.7s', color: 'bg-cyan-200' },
          { top: '58%', left: '88%', size: 3, delay: '0.4s', color: 'bg-violet-300' },
          { top: '48%', left: '12%', size: 3.5, delay: '1.5s', color: 'bg-sky-300' },
          { top: '18%', left: '85%', size: 2, delay: '2.1s', color: 'bg-cyan-400' },
          { top: '70%', left: '55%', size: 3, delay: '0.9s', color: 'bg-indigo-400' },
          { top: '38%', left: '68%', size: 2.5, delay: '3.5s', color: 'bg-violet-200' },
        ].map((pt, i) => (
          <div
            key={i}
            style={{
              top: pt.top,
              left: pt.left,
              width: `${pt.size}px`,
              height: `${pt.size}px`,
              animationDelay: pt.delay,
            }}
            className={`absolute rounded-full ${pt.color} shadow-[0_0_12px_currentColor] animate-pulse`}
          />
        ))}
      </div>

      {/* 5. Liquid Glass Frosted Vignette Border */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#080B10] via-transparent to-[#080B10] pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#080B10]/80 via-transparent to-[#080B10]/80 pointer-events-none" />
    </div>
  );
}
