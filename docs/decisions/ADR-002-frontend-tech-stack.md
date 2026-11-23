# ADR-002: Frontend Stack Selection (Next.js 15, Tailwind, Three.js)

## Status
Accepted

## Context
The platform must feel like an advanced AI operating system rather than a generic job board. It requires high-performance rendering of 3D audio visualizers, rapid responsiveness, and clean component modularity.

## Decision
Use Next.js 15+ (App Router), React 19, TypeScript strict mode, Tailwind CSS with shadcn/ui primitives, and React Three Fiber for the 3D Voice Orb.

## Consequences
- **Positive:** Rich developer ergonomics, fast server-side rendering for landing pages, and cinematic visual presence for the hackathon demo.
- **Negative:** Three.js and Canvas require careful lifecycle management to avoid memory leaks.
