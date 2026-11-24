'use client';

import React, { useState } from 'react';
import { Bot, Sparkles, Move3d } from 'lucide-react';

interface GenkubRobotProps {
  className?: string;
}

export function GenkubRobot({ className = '' }: GenkubRobotProps) {
  const [iframeLoaded, setIframeLoaded] = useState(false);

  return (
    <div
      className={`relative rounded-3xl border border-violet-500/30 bg-[#0A0E17]/90 p-4 sm:p-6 shadow-[0_0_60px_rgba(139,92,246,0.12)] backdrop-blur-xl overflow-hidden card-hover-lift ${className}`}
    >
      {/* Header telemetry & badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-white/[0.08]">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-violet-600/20 border border-violet-500/40 flex items-center justify-center text-violet-300">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white flex items-center gap-1.5">
              <span>GENKUB</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                Autonomous Greeting Agent
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Interactive 3D Collegiate Ambassador
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-2.5 py-1 rounded-full">
          <Move3d className="h-3 w-3 animate-spin" style={{ animationDuration: '6s' }} />
          <span>Interactive 3D Scene</span>
        </div>
      </div>

      {/* 3D Spline Iframe Container */}
      <div className="relative w-full h-[440px] sm:h-[500px] lg:h-[540px] rounded-2xl overflow-hidden bg-[#06080D] border border-white/[0.05]">
        {/* Loading state indicator */}
        {!iframeLoaded && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[#080B10] z-10">
            <div className="h-10 w-10 rounded-full border-2 border-violet-500/20 border-t-violet-400 animate-spin" />
            <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span>Awakening Genkub 3D Robot...</span>
            </div>
          </div>
        )}

        {/* Spline Greeting Robot Iframe */}
        <iframe
          src="https://my.spline.design/genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ/"
          frameBorder="0"
          width="100%"
          height="100%"
          title="GENKUB Greeting Robot - 3D Scene"
          allow="autoplay; fullscreen"
          onLoad={() => setIframeLoaded(true)}
          className={`w-full h-full transition-opacity duration-700 ${
            iframeLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      </div>

      {/* Interactive Helper Footer */}
      <div className="pt-3.5 mt-2 flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono gap-2">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Click and drag to rotate • Scroll to zoom</span>
        </span>
        <span className="text-slate-500">Live WebGL • Spline 3D</span>
      </div>
    </div>
  );
}
