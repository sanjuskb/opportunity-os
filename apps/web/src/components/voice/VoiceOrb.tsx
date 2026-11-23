'use client';

import React from 'react';

interface VoiceOrbProps {
  isListening?: boolean;
  isSpeaking?: boolean;
  language?: string;
  onToggle?: () => void;
}

export function VoiceOrb({
  isListening = false,
  isSpeaking = false,
  language = 'en',
  onToggle,
}: VoiceOrbProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <button
        type="button"
        onClick={onToggle}
        className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl focus:outline-none focus:ring-4 focus:ring-indigo-500/40 ${
          isSpeaking
            ? 'bg-gradient-to-r from-purple-600 to-pink-500 animate-pulse scale-105'
            : isListening
            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 animate-bounce'
            : 'bg-gradient-to-r from-indigo-600 to-slate-800 hover:scale-105'
        }`}
        aria-label="Voice Interaction Orb"
      >
        <span className="text-2xl text-white">🎙️</span>
      </button>
      <div className="text-xs font-medium text-slate-400 uppercase tracking-widest">
        {isSpeaking ? 'Speaking' : isListening ? 'Listening' : 'Tap to Speak'} • {language}
      </div>
    </div>
  );
}
