'use client';

import { useState, useEffect, useRef } from 'react';

export interface SceneLifecycleState {
  isIntersecting: boolean;
  isWebGLSupported: boolean;
  contextLost: boolean;
}

/**
 * Hook for managing WebGL scene lifecycle:
 * - Checks WebGL context support
 * - Monitors viewport intersection to pause/unmount offscreen 3D scenes
 * - Detects and handles WebGL context loss gracefully
 */
export function useSceneLifecycle(threshold = 0.15) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(true);
  const [isWebGLSupported, setIsWebGLSupported] = useState(true);
  const [contextLost, setContextLost] = useState(false);

  useEffect(() => {
    // 1. Check WebGL support
    try {
      const canvas = document.createElement('canvas');
      const gl =
        canvas.getContext('webgl2') ||
        canvas.getContext('webgl') ||
        canvas.getContext('experimental-webgl');
      if (!gl) {
        setIsWebGLSupported(false);
      }
    } catch {
      setIsWebGLSupported(false);
    }

    // 2. IntersectionObserver for viewport tracking
    if (!containerRef.current || typeof IntersectionObserver === 'undefined') {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      { threshold }
    );

    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
    };
  }, [threshold]);

  const handleContextLost = () => setContextLost(true);
  const handleContextRestored = () => setContextLost(false);

  return {
    containerRef,
    isIntersecting,
    isWebGLSupported,
    contextLost,
    handleContextLost,
    handleContextRestored,
  };
}
