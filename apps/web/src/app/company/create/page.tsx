'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { PlusCircle } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Select } from '../../../components/ui/Select';
import { useAuth } from '@/components/auth/AuthProvider';

export default function CreateOpportunityPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { user, apiClient } = useAuth();

  const [title, setTitle] = useState('');
  const [organization, setOrganization] = useState('');
  const [location, setLocation] = useState('Bangalore / Hybrid');
  const [type, setType] = useState('internship');
  const [stipendOrSalary, setStipendOrSalary] = useState('₹45,000 / month');
  const [sourceUrl, setSourceUrl] = useState('https://careers.example.com/jobs/intern');
  const [description, setDescription] = useState('');
  const [skillsStr, setSkillsStr] = useState('Python, FastAPI, PostgreSQL');
  const [minCgpa, setMinCgpa] = useState('7.5');
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setErrorMsg(null);
    setBusy(true);
    try {
      await apiClient.createCompanyOpportunity({
        title,
        organization,
        location,
        type,
        stipendOrSalary,
        description,
        sourceUrl,
        requiredSkills: skillsStr.split(',').map((s) => s.trim()).filter(Boolean),
        eligibleBatches: [2025, 2026, 2027, 2028],
        eligibleDegrees: ['B.Tech', 'M.Tech', 'MCA'],
        minCgpa: parseFloat(minCgpa) || 7.0,
      });
      void qc.invalidateQueries({ queryKey: ['opportunities'] });
      router.push('/company/dashboard');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to publish opportunity.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-3xl">
        <div className="pb-4 border-b border-slate-800">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Create New Opportunity</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Publish verified internships and roles directly into PostgreSQL.
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl border border-rose-500/40 bg-rose-950/30 text-xs text-rose-200">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Role Specifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input label="Opportunity Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Hiring Organization" value={organization} onChange={(e) => setOrganization(e.target.value)} required />
                <Input label="Location" value={location} onChange={(e) => setLocation(e.target.value)} required />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Select
                  label="Opportunity Type"
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  options={[
                    { value: 'internship', label: 'Internship' },
                    { value: 'full_time', label: 'Full Time' },
                    { value: 'fellowship', label: 'Fellowship' },
                    { value: 'hackathon', label: 'Hackathon' },
                  ]}
                />
                <Input label="Stipend / Salary" value={stipendOrSalary} onChange={(e) => setStipendOrSalary(e.target.value)} />
                <Input label="Minimum CGPA" type="number" step="0.1" value={minCgpa} onChange={(e) => setMinCgpa(e.target.value)} />
              </div>
              <Input label="Official Application URL" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} required />
              <Input label="Required Skills (Comma separated)" value={skillsStr} onChange={(e) => setSkillsStr(e.target.value)} required />
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                required
                placeholder="Role responsibilities and qualification criteria..."
                className="w-full rounded-lg border border-slate-800 bg-[#0B0F19] p-3 text-sm text-slate-200"
              />
            </CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" size="md" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" variant="glow" size="md" isLoading={busy} disabled={!user}>
              <PlusCircle className="h-4 w-4 mr-1.5" />
              <span>Publish to Ecosystem</span>
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
