'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Session, User } from '@supabase/supabase-js';
import { OpportunityApiClient } from '@opportunity-os/api-client';
import { createClient } from '@/lib/supabase/client';
import { getSupabasePublicConfig } from '@/lib/supabase/env';

interface AuthContextValue {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isConfigured: boolean;
  apiClient: OpportunityApiClient;
  refreshSession: () => Promise<Session | null>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isConfigured = Boolean(getSupabasePublicConfig());
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(isConfigured);

  const apiClient = useMemo(() => new OpportunityApiClient(API_BASE_URL), []);

  useEffect(() => {
    if (!isConfigured) {
      setLoading(false);
      return;
    }

    const supabase = createClient();
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      const activeSession = data.session ?? null;
      setSession(activeSession);
      setUser(activeSession?.user ?? null);
      apiClient.setToken(activeSession?.access_token ?? '');
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!mounted) return;
      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      apiClient.setToken(nextSession?.access_token ?? '');
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [apiClient, isConfigured]);

  const refreshSession = useCallback(async (): Promise<Session | null> => {
    if (!isConfigured) return null;
    const supabase = createClient();
    const { data, error } = await supabase.auth.refreshSession();
    if (error) {
      apiClient.setToken('');
      setSession(null);
      setUser(null);
      return null;
    }
    const nextSession = data.session ?? null;
    setSession(nextSession);
    setUser(nextSession?.user ?? null);
    apiClient.setToken(nextSession?.access_token ?? '');
    return nextSession;
  }, [apiClient, isConfigured]);

  useEffect(() => {
    apiClient.setUnauthorizedHandler(async () => {
      const nextSession = await refreshSession();
      return nextSession?.access_token ?? null;
    });
    return () => {
      apiClient.setUnauthorizedHandler(undefined);
    };
  }, [apiClient, refreshSession]);

  const signOut = useCallback(async () => {
    if (isConfigured) {
      const supabase = createClient();
      await supabase.auth.signOut();
    }
    apiClient.setToken('');
    setSession(null);
    setUser(null);
    router.push('/login');
    router.refresh();
  }, [apiClient, isConfigured, router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      session,
      loading,
      isConfigured,
      apiClient,
      refreshSession,
      signOut,
    }),
    [apiClient, isConfigured, loading, refreshSession, session, signOut, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider.');
  }
  return ctx;
}
