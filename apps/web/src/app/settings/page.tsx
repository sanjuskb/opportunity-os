'use client';

import { useAuth } from '@/components/auth/AuthProvider';

export default function SettingsPage() {
  const { user, loading, signOut } = useAuth();

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">System Settings &amp; Preferences</h1>
        <p className="text-slate-400">
          Manage voice language defaults, notifications, and privacy controls.
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Account Session
          </h2>
          {loading ? (
            <p className="text-sm text-slate-300 mt-1">Checking session...</p>
          ) : user ? (
            <p className="text-sm text-slate-200 mt-1">
              Signed in as <span className="font-medium text-indigo-300">{user.email}</span>
            </p>
          ) : (
            <p className="text-sm text-slate-400 mt-1">Not signed in.</p>
          )}
        </div>

        {user ? (
          <button
            type="button"
            onClick={signOut}
            className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm font-medium text-rose-300 hover:bg-rose-500/20 transition"
          >
            Sign Out
          </button>
        ) : (
          <a
            href="/login"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition"
          >
            Sign In
          </a>
        )}
      </section>
    </div>
  );
}
