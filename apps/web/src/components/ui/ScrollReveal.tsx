'use client';

import React, { useEffect, useRef, useState } from 'react';

/**
 * High-performance scroll reveal hook with full replay support.
 * When replay is true, the animation resets upon exiting the viewport,
 * allowing it to replay smoothly when the user scrolls back.
 */
export function useScrollReveal(threshold = 0.15, replay = true) {
  const ref = useRef<HTMLDivElement>(null);
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Check if element is currently in view on mount
    const rect = el.getBoundingClientRect();
    const inView = rect.top < window.innerHeight * 0.92 && rect.bottom > window.innerHeight * 0.08;
    if (inView) {
      setIsRevealed(true);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsRevealed(true);
            if (!replay) {
              observer.unobserve(el);
            }
          } else {
            if (replay) {
              // Only reset when element has scrolled sufficiently out of view
              const bounding = entry.boundingClientRect;
              if (bounding.top > window.innerHeight * 0.95 || bounding.bottom < 0) {
                setIsRevealed(false);
              }
            }
          }
        });
      },
      {
        threshold,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold, replay]);

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

/**
 * Splits text into words with whitespace-nowrap protection,
 * preventing words from ever breaking in half across lines.
 * Characters within each word animate with staggered letter reveals.
 */
export function SplitTextReveal({
  text,
  className = '',
  charClassName = '',
  delayOffsetMs = 60,
  charDelayMs = 22,
  isRevealed = true,
}: SplitTextRevealProps) {
  // Split into words so that words never break across line breaks
  const words = text.split(' ');
  let charCounter = 0;

  return (
    <span className={`inline ${className} ${isRevealed ? 'is-revealed' : ''}`}>
      {words.map((word, wordIndex) => {
        const wordChars = Array.from(word);
        const wordNode = (
          <span key={wordIndex} className="inline-block whitespace-nowrap">
            {wordChars.map((char) => {
              const currentDelay = delayOffsetMs + charCounter * charDelayMs;
              charCounter++;

              return (
                <span key={charCounter} className="text-mask">
                  <span
                    className={`text-char ${charClassName}`}
                    style={{
                      transitionDelay: isRevealed ? `${currentDelay}ms` : '0ms',
                    }}
                  >
                    {char}
                  </span>
                </span>
              );
            })}
          </span>
        );

        // Append a space after each word except the last
        if (wordIndex < words.length - 1) {
          charCounter++;
          return (
            <React.Fragment key={wordIndex}>
              {wordNode}
              <span className="inline-block">&nbsp;</span>
            </React.Fragment>
          );
        }

        return wordNode;
      })}
    </span>
  );
}

interface ScrollRevealCardProps {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
  replay?: boolean;
}

/**
 * Replayable card container that reveals with vertical drift and scale,
 * and resets cleanly when scrolled out of view.
 */
export function ScrollRevealCard({
  children,
  className = '',
  delayMs = 0,
  replay = true,
}: ScrollRevealCardProps) {
  const { ref, isRevealed } = useScrollReveal(0.08, replay);

  return (
    <div
      ref={ref}
      style={{
        transitionDelay: isRevealed ? `${delayMs}ms` : '0ms',
      }}
      className={`scroll-card ${isRevealed ? 'is-revealed' : ''} ${className}`}
    >
      {children}
    </div>
  );
}
