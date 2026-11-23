'use client';

import React, { useState } from 'react';
import { Settings, User, Globe, Bell, Shield, Save, Check } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { APP_CONFIG } from '@opportunity-os/shared-config';

export default function SettingsPage() {
  const { studentProfile, updateStudentProfile, activeLanguage, setActiveLanguage } = useMockStore();

  const [fullName, setFullName] = useState(studentProfile.fullName);
  const [headline, setHeadline] = useState(studentProfile.headline);
  const [collegeName, setCollegeName] = useState(studentProfile.collegeName);
  const [cgpa, setCgpa] = useState(studentProfile.cgpa?.toString() || '8.82');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateStudentProfile({
      fullName,
      headline,
      collegeName,
      cgpa: parseFloat(cgpa) || 8.0,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Account & Preferences</h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Manage your personal student details, preferred operating language, and verified credentials.
            </p>
          </div>
        </div>

        {savedSuccess && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>Profile settings saved successfully!</span>
          </div>
        )}

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
                <Input label="Professional Headline" value={headline} onChange={(e) => setHeadline(e.target.value)} required />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="College / University" value={collegeName} onChange={(e) => setCollegeName(e.target.value)} required />
                <Input label="Verified CGPA" value={cgpa} onChange={(e) => setCgpa(e.target.value)} required />
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
                onChange={(e) => setActiveLanguage(e.target.value as any)}
                options={APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => ({
                  value: l.code,
                  label: `${l.name} (${l.native})`,
                }))}
              />
              <p className="text-xs text-slate-400">
                All voice assistant answers and mock interview feedback will naturally switch to your selected language.
              </p>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button type="submit" variant="glow" size="md">
              <Save className="h-4 w-4 mr-1.5" />
              <span>Save Changes</span>
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
