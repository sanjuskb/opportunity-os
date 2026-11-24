'use client';

import React, { useState, useEffect } from 'react';

interface GenkubRobotProps {
  className?: string;
}

export function GenkubRobot({ className = '' }: GenkubRobotProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Safety timer: Ensure canvas becomes visible even if onLoad event is delayed
    const timer = setTimeout(() => {
      setIsLoaded(true);
    }, 2800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className={`relative w-full rounded-2xl border border-white/[0.09] bg-[#070A11] shadow-[0_0_60px_rgba(139,92,246,0.1)] overflow-hidden ${className}`}
    >
      {/* 3D Spline Interactive Canvas Container */}
      <div className="relative w-full h-[460px] sm:h-[500px] lg:h-[520px] bg-[#05070C]">
        {/* Subtle, non-blocking loading skeleton */}
        {!isLoaded && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[#070A11] z-10 transition-opacity duration-500">
            <div className="h-8 w-8 rounded-full border-2 border-violet-500/30 border-t-violet-400 animate-spin" />
            <span className="text-xs font-mono text-slate-400">Loading 3D Ambassador...</span>
          </div>
        )}

        {/* GENKUB Spline Verified Embed */}
        <iframe
          src="https://my.spline.design/genkubgreetingrobot-EOlN5of6xh4LRe3SwQPBBHXH/"
          frameBorder="0"
          width="100%"
          height="100%"
          title="GENKUB Autonomous Agent"
          allow="autoplay; fullscreen"
          onLoad={() => setIsLoaded(true)}
          className={`w-full h-full transition-opacity duration-700 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      </div>

      {/* Discreet interaction footer */}
      <div className="px-5 py-3 border-t border-white/[0.06] bg-[#05070A] flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span>Interactive 3D • Click & drag to orbit</span>
        </span>
        <span className="text-slate-500">Spline Real-Time Engine</span>
      </div>
    </div>
  );
}
