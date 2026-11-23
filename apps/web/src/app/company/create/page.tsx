'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PlusCircle, Sparkles, ArrowRight, Building2, CheckCircle2 } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Select } from '../../../components/ui/Select';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function CreateOpportunityPage() {
  const router = useRouter();
  const { createOpportunity } = useMockStore();

  const [title, setTitle] = useState('');
  const [organization, setOrganization] = useState('Google India');
  const [location, setLocation] = useState('Bangalore / Hybrid');
  const [type, setType] = useState('internship');
  const [stipendOrSalary, setStipendOrSalary] = useState('₹50,000 / month');
  const [deadline, setDeadline] = useState('2026-12-31');
  const [description, setDescription] = useState('');
  const [skillsStr, setSkillsStr] = useState('Python, PyTorch, Transformers, System Design');
  const [minCgpa, setMinCgpa] = useState('8.0');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createOpportunity({
      title,
      organization,
      location,
      type: type as any,
      stipendOrSalary,
      deadline,
      description,
      sourceUrl: 'https://careers.google.com',
      sourceProvider: 'direct_portal',
      requiredSkills: skillsStr.split(',').map((s) => s.trim()).filter(Boolean),
      eligibleBatches: [2025, 2026, 2027],
      eligibleDegrees: ['B.Tech', 'M.Tech', 'Dual Degree'],
      minCgpa: parseFloat(minCgpa) || 7.5,
    });
    router.push('/company/dashboard');
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-3xl">
        <div className="pb-4 border-b border-slate-800">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Create New Opportunity</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Publish verified internships, fellowships, and full-time roles directly to 50,000+ Indian students.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Role Specifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Opportunity Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                placeholder="e.g. AI Research Intern — Indic LLMs"
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Hiring Organization"
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  required
                />
                <Input
                  label="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  required
                />
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
                <Input
                  label="Stipend / Salary"
                  value={stipendOrSalary}
                  onChange={(e) => setStipendOrSalary(e.target.value)}
                  required
                />
                <Input
                  label="Application Deadline"
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Role Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  required
                  placeholder="Describe key responsibilities, mentor guidance, and learning outcomes..."
                  className="w-full rounded-lg border border-slate-800 bg-[#0B0F19] p-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Eligibility & Skill Criteria</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Required Skills (Comma separated)"
                value={skillsStr}
                onChange={(e) => setSkillsStr(e.target.value)}
                required
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Minimum CGPA Requirement"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  value={minCgpa}
                  onChange={(e) => setMinCgpa(e.target.value)}
                />
                <div className="text-xs text-slate-400 self-center pt-4">
                  Autonomous agents will pre-screen and verify students meeting this cutoff.
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" size="md" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button type="submit" variant="glow" size="md">
              <PlusCircle className="h-4 w-4 mr-1.5" />
              <span>Publish to Ecosystem</span>
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
