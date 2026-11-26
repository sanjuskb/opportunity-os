'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Globe, Save, Check, Shield, User } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useStudentProfile,
  useUpdateUserProfile,
  useUpsertStudentProfile,
  useUserProfile,
} from '@/lib/queries/useOpportunityOs';

export default function SettingsPage() {
  const { user, loading, signOut } = useAuth();
  const { activeLanguage, setActiveLanguage } = useMockStore();
  const { data: userProfile } = useUserProfile();
  const { data: studentProfile } = useStudentProfile();
  const updateProfile = useUpdateUserProfile();
  const upsertStudent = useUpsertStudentProfile();

  const [fullName, setFullName] = useState('');
  const [collegeName, setCollegeName] = useState('');
  const [degree, setDegree] = useState('B.Tech');
  const [branch, setBranch] = useState('Computer Science');
  const [graduationYear, setGraduationYear] = useState(2027);
  const [cgpa, setCgpa] = useState('8.5');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (userProfile) {
      setFullName(userProfile.fullName ?? '');
      if (userProfile.preferredLanguage) {
        setActiveLanguage(userProfile.preferredLanguage as typeof activeLanguage);
      }
    }
  }, [userProfile, setActiveLanguage]);

  useEffect(() => {
    if (studentProfile) {
      setCollegeName(studentProfile.collegeName ?? '');
      setDegree(studentProfile.degree ?? 'B.Tech');
      setBranch(studentProfile.branch ?? 'Computer Science');
      setGraduationYear(studentProfile.graduationYear ?? 2027);
      setCgpa(studentProfile.cgpa != null ? String(studentProfile.cgpa) : '8.5');
    }
  }, [studentProfile]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setErrorMsg(null);
    setSavedSuccess(false);
    try {
      await updateProfile.mutateAsync({
        fullName: fullName.trim() || undefined,
        preferredLanguage: activeLanguage,
      });
      if (collegeName.trim()) {
        await upsertStudent.mutateAsync({
          collegeName: collegeName.trim(),
          degree: degree.trim() || 'B.Tech',
          branch: branch.trim() || 'Computer Science',
          graduationYear,
          cgpa: parseFloat(cgpa) || undefined,
        });
      }
      setSavedSuccess(true);
      window.setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to save preferences.');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Account & Preferences</h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Manage your personal academic credentials and 9-language Voice Copilot settings.
            </p>
          </div>
        </div>

        {savedSuccess && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>Profile settings saved to PostgreSQL successfully.</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-200 text-xs">
            {errorMsg}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <span>Account Session (Supabase Auth)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              {loading ? (
                <p className="text-sm text-slate-300">Checking session...</p>
              ) : user ? (
                <p className="text-sm text-slate-200">
                  Signed in as <span className="font-medium text-cyan-300">{user.email}</span>
                </p>
              ) : (
                <p className="text-sm text-slate-400">Not signed in.</p>
              )}
            </div>

            {user ? (
              <button
                type="button"
                onClick={signOut}
                className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-xs font-semibold text-rose-300 hover:bg-rose-500/20 transition"
              >
                Sign Out
              </button>
            ) : (
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition"
              >
                Sign In
              </Link>
            )}
          </CardContent>
        </Card>

        <form onSubmit={handleSave} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-4 w-4 text-cyan-400" />
                <span>Personal & Academic Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                <Input label="College / University" value={collegeName} onChange={(e) => setCollegeName(e.target.value)} />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Input label="Degree" value={degree} onChange={(e) => setDegree(e.target.value)} />
                <Input label="Branch / Major" value={branch} onChange={(e) => setBranch(e.target.value)} />
                <Input label="Verified CGPA" value={cgpa} onChange={(e) => setCgpa(e.target.value)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-violet-400" />
                <span>Language & Voice Preferences</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select
                label="Operating & Voice AI Language"
                value={activeLanguage}
                onChange={(e) => setActiveLanguage(e.target.value as typeof activeLanguage)}
                options={APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => ({
                  value: l.code,
                  label: `${l.name} (${l.native})`,
                }))}
              />
              <p className="text-xs text-slate-400">
                All voice assistant answers and mock interview feedback adapt across all 9 supported Indian languages.
              </p>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button
              type="submit"
              variant="glow"
              size="md"
              isLoading={updateProfile.isPending || upsertStudent.isPending}
              disabled={!user}
            >
              <Save className="h-4 w-4 mr-1.5" />
              <span>Save Changes</span>
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
