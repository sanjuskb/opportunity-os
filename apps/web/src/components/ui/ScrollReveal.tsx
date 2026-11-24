'use client';

import React, { useEffect, useRef, useState } from 'react';

export function useScrollReveal(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null);
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Check if element is already in viewport
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight * 0.95 && rect.bottom > 0) {
      setIsRevealed(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsRevealed(true);
          observer.unobserve(el);
        }
      },
      {
        threshold,
        rootMargin: '0px 0px -60px 0px',
      }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, isRevealed };
}

interface SplitTextRevealProps {
  text: string;
  className?: string;
  charClassName?: string;
  delayOffsetMs?: number;
  charDelayMs?: number;
  isRevealed?: boolean;
}

export function SplitTextReveal({
  text,
  className = '',
  charClassName = '',
  delayOffsetMs = 80,
  charDelayMs = 28,
  isRevealed = true,
}: SplitTextRevealProps) {
  const characters = Array.from(text);

  return (
    <span className={`inline-block ${className} ${isRevealed ? 'is-revealed' : ''}`}>
      {characters.map((char, index) => {
        if (char === ' ') {
          return (
            <span key={index} className="inline-block text-mask">
              <span className="text-char">&nbsp;</span>
            </span>
          );
        }

        const delay = delayOffsetMs + index * charDelayMs;

        return (
          <span key={index} className="text-mask">
            <span
              className={`text-char ${charClassName}`}
              style={{
                transitionDelay: `${delay}ms`,
              }}
            >
              {char}
            </span>
          </span>
        );
      })}
    </span>
  );
}

interface ScrollRevealCardProps {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
}

export function ScrollRevealCard({
  children,
  className = '',
  delayMs = 0,
}: ScrollRevealCardProps) {
  const { ref, isRevealed } = useScrollReveal(0.1);

  return (
    <div
      ref={ref}
      style={{
        transitionDelay: `${delayMs}ms`,
      }}
      className={`scroll-card ${isRevealed ? 'is-revealed' : ''} ${className}`}
    >
      {children}
    </div>
  );
}

interface BackgroundChapterNoProps {
  number: string;
  className?: string;
}

export function BackgroundChapterNo({ number, className = '' }: BackgroundChapterNoProps) {
  const { ref, isRevealed } = useScrollReveal(0.05);

  return (
    <div
      ref={ref}
      className={`bg-chapter-no ${className} ${
        isRevealed ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
      aria-hidden="true"
    >
      {number}
    </div>
  );
}
