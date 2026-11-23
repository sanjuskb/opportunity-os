'use client';

import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { EcosystemRole } from '../hero/RoleSwitcher';

interface EcosystemSceneProps {
  activeHub: EcosystemRole | 'core';
  onSelectHub: (hub: EcosystemRole | 'core') => void;
}

export function EcosystemScene({ activeHub, onSelectHub }: EcosystemSceneProps) {
  // Central AI Core Animation
  const coreRef = useRef<THREE.Group>(null);
  const coreOuterRef = useRef<THREE.Mesh>(null);
  const shuttlesRef = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (coreRef.current) {
      coreRef.current.rotation.y += delta * 0.4;
      coreRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.8) * 0.1;
    }
    if (coreOuterRef.current) {
      coreOuterRef.current.rotation.y -= delta * 0.25;
      coreOuterRef.current.rotation.z += delta * 0.15;
    }
    if (shuttlesRef.current) {
      shuttlesRef.current.children.forEach((child, idx) => {
        const speed = 0.8 + idx * 0.1;
        const offset = (state.clock.elapsedTime * speed + idx * 1.5) % 4;
        const norm = offset / 4;
        // Ping-pong along pathway (radius 0.6 to 2.8)
        const radius = 0.6 + Math.abs(Math.sin(norm * Math.PI)) * 2.2;
        const angle = (idx * Math.PI) / 2;
        child.position.x = Math.cos(angle) * radius;
        child.position.z = Math.sin(angle) * radius;
        child.position.y = 0.35 + Math.sin(state.clock.elapsedTime * 3 + idx) * 0.05;
        child.rotation.y += delta * 2;
      });
    }
  });

  const handlePointerOver = () => {
    if (typeof document !== 'undefined') {
      document.body.style.cursor = 'pointer';
    }
  };

  const handlePointerOut = () => {
    if (typeof document !== 'undefined') {
      document.body.style.cursor = 'auto';
    }
  };

  return (
    <>
      {/* Cinematic Lighting */}
      <ambientLight intensity={0.65} color="#64748B" />
      <directionalLight position={[10, 15, 8]} intensity={1.2} color="#F8FAFC" />
      <pointLight position={[0, 1.5, 0]} intensity={3.5} distance={8} color="#A855F7" />

      {/* Camera Controls */}
      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={6}
        maxDistance={13}
        maxPolarAngle={Math.PI / 2.15}
        minPolarAngle={Math.PI / 6}
        autoRotate={activeHub === 'core'}
        autoRotateSpeed={0.6}
        dampingFactor={0.05}
      />

      {/* Group centered on maquette */}
      <group position={[0, -0.6, 0]}>
        {/* Monolithic Obsidian Baseplate */}
        <mesh position={[0, -0.15, 0]} receiveShadow>
          <cylinderGeometry args={[4.2, 4.4, 0.3, 48]} />
          <meshStandardMaterial
            color="#0B0F19"
            metalness={0.85}
            roughness={0.25}
          />
        </mesh>

        {/* Baseplate Chamfered Ring */}
        <mesh position={[0, 0.01, 0]}>
          <ringGeometry args={[3.8, 4.1, 48]} />
          <meshStandardMaterial
            color="#1E293B"
            metalness={0.9}
            roughness={0.3}
            side={THREE.DoubleSide}
          />
        </mesh>

        {/* Recessed Optical Pathway Conduits */}
        {/* 1. Student Pathway (West / -X) */}
        <mesh position={[-1.7, 0.02, 0]}>
          <boxGeometry args={[2.6, 0.02, 0.14]} />
          <meshStandardMaterial
            color="#06B6D4"
            emissive="#06B6D4"
            emissiveIntensity={activeHub === 'students' ? 2.5 : 1.0}
            toneMapped={false}
          />
        </mesh>

        {/* 2. Company Pathway (East / +X) */}
        <mesh position={[1.7, 0.02, 0]}>
          <boxGeometry args={[2.6, 0.02, 0.14]} />
          <meshStandardMaterial
            color="#3B82F6"
            emissive="#3B82F6"
            emissiveIntensity={activeHub === 'companies' ? 2.5 : 1.0}
            toneMapped={false}
          />
        </mesh>

        {/* 3. University Pathway (North / -Z) */}
        <mesh position={[0, 0.02, -1.7]}>
          <boxGeometry args={[0.14, 0.02, 2.6]} />
          <meshStandardMaterial
            color="#10B981"
            emissive="#10B981"
            emissiveIntensity={activeHub === 'universities' ? 2.5 : 1.0}
            toneMapped={false}
          />
        </mesh>

        {/* 4. Opportunity Pathway (South / +Z) */}
        <mesh position={[0, 0.02, 1.7]}>
          <boxGeometry args={[0.14, 0.02, 2.6]} />
          <meshStandardMaterial
            color="#F59E0B"
            emissive="#F59E0B"
            emissiveIntensity={activeHub === 'opportunities' ? 2.5 : 1.0}
            toneMapped={false}
          />
        </mesh>

        {/* Autonomous Agent Shuttles */}
        <group ref={shuttlesRef}>
          {/* Shuttle 0: Student pathway */}
          <mesh>
            <octahedronGeometry args={[0.09, 0]} />
            <meshStandardMaterial color="#38BDF8" emissive="#38BDF8" emissiveIntensity={2} />
          </mesh>
          {/* Shuttle 1: Opportunity pathway */}
          <mesh>
            <octahedronGeometry args={[0.09, 0]} />
            <meshStandardMaterial color="#FBBF24" emissive="#FBBF24" emissiveIntensity={2} />
          </mesh>
          {/* Shuttle 2: Company pathway */}
          <mesh>
            <octahedronGeometry args={[0.09, 0]} />
            <meshStandardMaterial color="#60A5FA" emissive="#60A5FA" emissiveIntensity={2} />
          </mesh>
          {/* Shuttle 3: University pathway */}
          <mesh>
            <octahedronGeometry args={[0.09, 0]} />
            <meshStandardMaterial color="#34D399" emissive="#34D399" emissiveIntensity={2} />
          </mesh>
        </group>

        {/* Central AI Intelligence Core */}
        <group
          ref={coreRef}
          position={[0, 0.65, 0]}
          onClick={(e) => {
            e.stopPropagation();
            onSelectHub('core');
          }}
          onPointerOver={handlePointerOver}
          onPointerOut={handlePointerOut}
        >
          {/* Inner pulsating core */}
          <mesh>
            <sphereGeometry args={[0.42, 32, 32]} />
            <meshStandardMaterial
              color="#6366F1"
              emissive="#8B5CF6"
              emissiveIntensity={1.8}
              roughness={0.2}
              metalness={0.7}
            />
          </mesh>

          {/* Outer wireframe shell (Inspired by Reactive Orb) */}
          <mesh ref={coreOuterRef}>
            <icosahedronGeometry args={[0.62, 1]} />
            <meshStandardMaterial
              color="#A855F7"
              emissive="#C084FC"
              emissiveIntensity={1.2}
              wireframe
              transparent
              opacity={0.75}
            />
          </mesh>

          {/* Central Core Pedestal */}
          <mesh position={[0, -0.45, 0]}>
            <cylinderGeometry args={[0.5, 0.65, 0.35, 24]} />
            <meshStandardMaterial color="#0F172A" metalness={0.9} roughness={0.2} />
          </mesh>
        </group>

        {/* Hub 1: Students (West / -X) */}
        <group
          position={[-3.0, 0.4, 0]}
          onClick={(e) => {
            e.stopPropagation();
            onSelectHub('students');
          }}
          onPointerOver={handlePointerOver}
          onPointerOut={handlePointerOut}
        >
          <mesh position={[0, 0.25, 0]}>
            <cylinderGeometry args={[0.55, 0.65, 0.5, 6]} />
            <meshStandardMaterial
              color="#0F172A"
              metalness={0.7}
              roughness={0.3}
            />
          </mesh>
          {/* Cyan Glow Trim */}
          <mesh position={[0, 0.55, 0]}>
            <torusGeometry args={[0.45, 0.04, 16, 32]} />
            <meshStandardMaterial
              color="#06B6D4"
              emissive="#06B6D4"
              emissiveIntensity={activeHub === 'students' ? 3.0 : 1.2}
            />
          </mesh>
          <mesh position={[0, 0.65, 0]}>
            <coneGeometry args={[0.25, 0.35, 6]} />
            <meshStandardMaterial color="#06B6D4" metalness={0.9} roughness={0.1} />
          </mesh>
        </group>

        {/* Hub 2: Companies (East / +X) */}
        <group
          position={[3.0, 0.45, 0]}
          onClick={(e) => {
            e.stopPropagation();
            onSelectHub('companies');
          }}
          onPointerOver={handlePointerOver}
          onPointerOut={handlePointerOut}
        >
          <mesh position={[0, 0.35, 0]}>
            <boxGeometry args={[0.8, 0.8, 0.8]} />
            <meshStandardMaterial
              color="#1E293B"
              metalness={0.8}
              roughness={0.2}
            />
          </mesh>
          {/* Sapphire Glow Trim */}
          <mesh position={[0, 0.8, 0]}>
            <boxGeometry args={[0.6, 0.05, 0.6]} />
            <meshStandardMaterial
              color="#3B82F6"
              emissive="#3B82F6"
              emissiveIntensity={activeHub === 'companies' ? 3.0 : 1.2}
            />
          </mesh>
        </group>

        {/* Hub 3: Universities (North / -Z) */}
        <group
          position={[0, 0.4, -3.0]}
          onClick={(e) => {
            e.stopPropagation();
            onSelectHub('universities');
          }}
          onPointerOver={handlePointerOver}
          onPointerOut={handlePointerOut}
        >
          <mesh position={[0, 0.25, 0]}>
            <cylinderGeometry args={[0.6, 0.65, 0.5, 32]} />
            <meshStandardMaterial
              color="#0F172A"
              metalness={0.7}
              roughness={0.3}
            />
          </mesh>
          {/* Emerald Dome & Ring */}
          <mesh position={[0, 0.55, 0]}>
            <sphereGeometry args={[0.45, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
            <meshStandardMaterial
              color="#10B981"
              emissive="#10B981"
              emissiveIntensity={activeHub === 'universities' ? 2.5 : 1.0}
              roughness={0.2}
            />
          </mesh>
        </group>

        {/* Hub 4: Opportunities (South / +Z) */}
        <group
          position={[0, 0.4, 3.0]}
          onClick={(e) => {
            e.stopPropagation();
            onSelectHub('opportunities');
          }}
          onPointerOver={handlePointerOver}
          onPointerOut={handlePointerOut}
        >
          <mesh position={[0, 0.25, 0]}>
            <cylinderGeometry args={[0.65, 0.75, 0.45, 8]} />
            <meshStandardMaterial
              color="#1E293B"
              metalness={0.75}
              roughness={0.25}
            />
          </mesh>
          {/* Amber Ingestion Portal Ring */}
          <mesh position={[0, 0.52, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.42, 0.05, 16, 32]} />
            <meshStandardMaterial
              color="#F59E0B"
              emissive="#F59E0B"
              emissiveIntensity={activeHub === 'opportunities' ? 3.0 : 1.2}
            />
          </mesh>
        </group>
      </group>
    </>
  );
}
