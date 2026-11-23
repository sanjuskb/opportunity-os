'use client';

import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { EcosystemScene } from './EcosystemScene';
import { CampusHUD } from '../hero/CampusHUD';
import { CampusFallback } from '../hero/CampusFallback';
import { useReducedMotion } from '../../3d/hooks/useReducedMotion';
import { useSceneLifecycle } from '../../3d/hooks/useSceneLifecycle';
import type { EcosystemRole } from '../hero/RoleSwitcher';

interface EcosystemCampusProps {
  activeRole?: EcosystemRole;
  onRoleChange?: (role: EcosystemRole) => void;
}

export function EcosystemCampus({
  activeRole = 'students',
  onRoleChange,
}: EcosystemCampusProps) {
  const [selectedHub, setSelectedHub] = useState<EcosystemRole | 'core'>(activeRole);
  const prefersReducedMotion = useReducedMotion();
  const { containerRef, isIntersecting, isWebGLSupported, contextLost } = useSceneLifecycle();

  // Sync external role change with internal selection
  React.useEffect(() => {
    setSelectedHub(activeRole);
  }, [activeRole]);

  const handleSelectHub = (hub: EcosystemRole | 'core') => {
    setSelectedHub(hub);
    if (hub !== 'core' && onRoleChange) {
      onRoleChange(hub);
    }
  };

  const handleReset = () => {
    setSelectedHub('core');
  };

  // If WebGL is not supported, context was lost, or user prefers reduced motion, render the instant fallback
  if (!isWebGLSupported || contextLost || prefersReducedMotion) {
    return (
      <div className="relative w-full h-[450px] sm:h-[520px] lg:h-[600px]">
        <CampusFallback
          activeHub={selectedHub}
          onSelectHub={(h) => handleSelectHub(h)}
        />
        <CampusHUD
          activeHub={selectedHub}
          onReset={handleReset}
          onSelectHub={(h) => handleSelectHub(h)}
        />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[450px] sm:h-[520px] lg:h-[600px] rounded-2xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-2xl"
    >
      {/* 3D Canvas only active when intersecting viewport */}
      {isIntersecting ? (
        <Suspense fallback={<CampusFallback activeHub={selectedHub} />}>
          <Canvas
            camera={{ position: [7.5, 8.5, 7.5], fov: 38 }}
            dpr={[1, 2]}
            gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
            className="w-full h-full cursor-grab active:cursor-grabbing"
          >
            <color attach="background" args={['#0B0F19']} />
            <EcosystemScene
              activeHub={selectedHub}
              onSelectHub={handleSelectHub}
            />
          </Canvas>
        </Suspense>
      ) : (
        <CampusFallback activeHub={selectedHub} />
      )}

      {/* Accessible DOM Overlay */}
      <CampusHUD
        activeHub={selectedHub}
        onReset={handleReset}
        onSelectHub={(h) => handleSelectHub(h)}
      />
    </div>
  );
}
