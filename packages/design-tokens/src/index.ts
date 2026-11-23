export const colors = {
  brand: {
    primary: '#4F46E5', // Indigo
    primaryHover: '#4338CA',
    accent: '#06B6D4',  // Cyan
    glow: '#818CF8',
  },
  surface: {
    background: '#090D16',
    card: '#111827',
    border: '#1F2937',
    input: '#1E293B',
  },
  status: {
    eligible: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',
  },
  voice: {
    activeOrb: '#6366F1',
    listeningWave: '#38BDF8',
    speakingWave: '#A855F7',
  },
  // Approved Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette) Ecosystem Mapping
  ecosystem: {
    students: '#06B6D4',       // Cyan: Student profiles, Career Passports, resume intelligence
    companies: '#3B82F6',      // Sapphire / Indigo: Hiring partners, verified job posts
    universities: '#10B981',   // Emerald: Academic institutions, degree verification
    opportunities: '#F59E0B',  // Amber: Live internship/scholarship/grant discovery
    aiCore: '#8B5CF6',         // Violet / Indigo: Central AI coordination & agent matching
  },
} as const;

export const materials3D = {
  baseplate: '#0B0F19',        // Dark anodised obsidian baseplate
  titanium: '#94A3B8',         // Satin titanium
  slateStructure: '#1E293B',   // Dark slate architectural structures
  glass: 'rgba(30, 41, 59, 0.65)', // Subtle frosted glass
  opticalChannel: '#020617',   // Recessed optical channel bed
  emissivePath: '#38BDF8',     // Cyan pathway illumination
} as const;

export const typography = {
  fontSans: 'var(--font-sans, system-ui, sans-serif)',
  fontMono: 'var(--font-mono, monospace)',
} as const;
