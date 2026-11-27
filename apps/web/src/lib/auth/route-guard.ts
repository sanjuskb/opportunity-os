export const PROTECTED_PREFIXES = [
  '/overview',
  '/onboarding',
  '/role-selection',
  '/career-passport',
  '/opportunities',
  '/resume',
  '/applications',
  '/interview',
  '/analytics',
  '/notifications',
  '/settings',
  '/agent-control-center',
  '/voice-ai',
  '/company',
  '/university',
] as const;

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

export function shouldFailClosedWithoutConfig(
  nodeEnv: string | undefined = process.env.NODE_ENV,
  allowDevBypass: string | undefined = process.env.NEXT_PUBLIC_ALLOW_DEV_BYPASS
): boolean {
  if (nodeEnv === 'production') {
    return true;
  }
  return allowDevBypass !== 'true';
}
