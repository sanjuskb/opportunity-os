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
  }
} as const;

export const typography = {
  fontSans: 'var(--font-sans, system-ui, sans-serif)',
  fontMono: 'var(--font-mono, monospace)',
} as const;
