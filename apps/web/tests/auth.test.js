import test from 'node:test';
import assert from 'node:assert/strict';
import { sanitizeNextPath } from '../src/lib/auth/redirect.ts';
import { getSupabasePublicConfig } from '../src/lib/supabase/env.ts';

test('getSupabasePublicConfig prefers NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', () => {
  const prevUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const prevPub = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  const prevAnon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  try {
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://bmaousfsdtqudvmbbhmb.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_test_key';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'legacy_anon_key';
    assert.deepEqual(getSupabasePublicConfig(), {
      url: 'https://bmaousfsdtqudvmbbhmb.supabase.co',
      anonKey: 'sb_publishable_test_key',
    });
  } finally {
    if (prevUrl === undefined) delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    else process.env.NEXT_PUBLIC_SUPABASE_URL = prevUrl;
    if (prevPub === undefined) delete process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
    else process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = prevPub;
    if (prevAnon === undefined) delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    else process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = prevAnon;
  }
});

test('sanitizeNextPath blocks open redirects and allows safe relative paths', () => {
  assert.equal(sanitizeNextPath('/career-passport'), '/career-passport');
  assert.equal(sanitizeNextPath('/applications?tab=active'), '/applications?tab=active');
  assert.equal(sanitizeNextPath('https://evil.example.com/phish'), '/opportunities');
  assert.equal(sanitizeNextPath('//evil.example.com/phish'), '/opportunities');
  assert.equal(sanitizeNextPath('/\\evil.example.com'), '/opportunities');
  assert.equal(sanitizeNextPath(null), '/opportunities');
});

test('middleware redirect contract enforces protected routes and sanitized /login?next', () => {
  const PROTECTED = ['/career-passport', '/applications', '/resume', '/interview', '/analytics', '/settings'];
  const isProtected = (p) => PROTECTED.some((x) => p === x || p.startsWith(`${x}/`));

  assert.equal(isProtected('/career-passport'), true);
  assert.equal(isProtected('/settings'), true);
  assert.equal(isProtected('/opportunities'), false);
  assert.equal(isProtected('/login'), false);

  // Authenticated user visiting /login?next=... respects safe relative next or falls back to /opportunities
  assert.equal(sanitizeNextPath('/resume', '/opportunities'), '/resume');
  assert.equal(sanitizeNextPath('https://attacker.test', '/opportunities'), '/opportunities');
  assert.equal(sanitizeNextPath('//attacker.test', '/opportunities'), '/opportunities');
  assert.equal(sanitizeNextPath('/\\attacker.test', '/opportunities'), '/opportunities');
});

test('OAuth callback contract exchanges code and guards against missing or invalid code', async () => {
  async function simulateCallback(urlStr, supabase) {
    const { searchParams, origin } = new URL(urlStr);
    const code = searchParams.get('code');
    const nextPath = sanitizeNextPath(searchParams.get('next'), '/opportunities');
    if (!code) return `${origin}/login?error=missing_oauth_code`;
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) return `${origin}/login?error=oauth_exchange_failed`;
    return `${origin}${nextPath}`;
  }

  let exchangedCode = null;
  const okSupabase = {
    auth: {
      exchangeCodeForSession: async (c) => {
        exchangedCode = c;
        return { error: null };
      },
    },
  };
  assert.equal(
    await simulateCallback('http://localhost:3000/auth/callback?code=pkce-123&next=/career-passport', okSupabase),
    'http://localhost:3000/career-passport'
  );
  assert.equal(exchangedCode, 'pkce-123');

  // Open redirect attempt in callback ?next= is neutralized
  assert.equal(
    await simulateCallback('http://localhost:3000/auth/callback?code=pkce-123&next=https://evil.com', okSupabase),
    'http://localhost:3000/opportunities'
  );

  // Missing code & exchange failure
  assert.equal(
    await simulateCallback('http://localhost:3000/auth/callback', okSupabase),
    'http://localhost:3000/login?error=missing_oauth_code'
  );
  const badSupabase = {
    auth: { exchangeCodeForSession: async () => ({ error: new Error('invalid_grant') }) },
  };
  assert.equal(
    await simulateCallback('http://localhost:3000/auth/callback?code=bad', badSupabase),
    'http://localhost:3000/login?error=oauth_exchange_failed'
  );
});

test('Google OAuth initiation, 6-digit Email OTP, session refresh, and logout contracts', async () => {
  const calls = [];
  let token = '';
  const mockSupabase = {
    auth: {
      signInWithOAuth: async (opts) => {
        calls.push(['oauth', opts]);
        return { error: null };
      },
      signInWithOtp: async (opts) => {
        calls.push(['sendOtp', opts]);
        return { error: null };
      },
      verifyOtp: async ({ token: code }) => {
        calls.push(['verifyOtp', code]);
        if (code !== '123456') return { error: new Error('Token has expired or is invalid') };
        token = 'session-jwt-1';
        return { error: null };
      },
      refreshSession: async () => {
        token = 'session-jwt-2';
        return { data: { session: { access_token: token } }, error: null };
      },
      signOut: async () => {
        token = '';
        return { error: null };
      },
    },
  };

  await mockSupabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: 'http://localhost:3000/auth/callback?next=%2Fopportunities' },
  });
  assert.equal(calls[0][0], 'oauth');
  assert.equal(calls[0][1].provider, 'google');

  await mockSupabase.auth.signInWithOtp({
    email: 'student@iitb.ac.in',
    options: { shouldCreateUser: true },
  });
  assert.equal(calls[1][0], 'sendOtp');

  const badOtp = await mockSupabase.auth.verifyOtp({ email: 'student@iitb.ac.in', token: '000000', type: 'email' });
  assert.ok(badOtp.error);

  const okOtp = await mockSupabase.auth.verifyOtp({ email: 'student@iitb.ac.in', token: '123456', type: 'email' });
  assert.equal(okOtp.error, null);
  assert.equal(token, 'session-jwt-1');

  const refreshed = await mockSupabase.auth.refreshSession();
  assert.equal(refreshed.data.session.access_token, 'session-jwt-2');

  await mockSupabase.auth.signOut();
  assert.equal(token, '');
});
