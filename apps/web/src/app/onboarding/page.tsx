'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, ArrowRight, ArrowLeft, Globe, GraduationCap, Wrench, Compass, Sparkles, Award } from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { useAuth } from '@/components/auth/AuthProvider';
import { useUpdateUserProfile, useUpsertStudentProfile } from '@/lib/queries/useOpportunityOs';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { studentProfile, updateStudentProfile, setActiveLanguage, activeLanguage, userRole } = useMockStore();
  const updateProfile = useUpdateUserProfile();
  const upsertStudent = useUpsertStudentProfile();
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    preferredLanguage: activeLanguage,
    fullName: studentProfile.fullName,
    collegeName: studentProfile.collegeName,
    degree: studentProfile.degree,
    branch: studentProfile.branch,
    graduationYear: studentProfile.graduationYear,
    cgpa: studentProfile.cgpa || 8.5,
    skills: studentProfile.skills,
    desiredRole: 'AI & Full Stack Engineer',
    desiredLocation: 'Bangalore / Remote',
    minStipend: '₹35,000 / month',
  });

  const [skillInput, setSkillInput] = useState('');

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
      setFormData({ ...formData, skills: [...formData.skills, skillInput.trim()] });
      setSkillInput('');
    }
  };

  const removeSkill = (sk: string) => {
    setFormData({ ...formData, skills: formData.skills.filter((s) => s !== sk) });
  };

  const handleFinish = async () => {
    setErrorMsg(null);
    updateStudentProfile({
      fullName: formData.fullName,
      collegeName: formData.collegeName,
      degree: formData.degree,
      branch: formData.branch,
      graduationYear: formData.graduationYear,
      cgpa: formData.cgpa,
      skills: formData.skills,
      preferredLanguage: formData.preferredLanguage as typeof activeLanguage,
    });
    if (user) {
      setSaving(true);
      try {
        await updateProfile.mutateAsync({
          fullName: formData.fullName,
          preferredLanguage: formData.preferredLanguage,
          userRole,
        });
        await upsertStudent.mutateAsync({
          collegeName: formData.collegeName,
          degree: formData.degree,
          branch: formData.branch,
          graduationYear: formData.graduationYear,
          cgpa: formData.cgpa,
          skills: formData.skills,
          preferredLocations: formData.desiredLocation.split(',').map((s) => s.trim()).filter(Boolean),
          bio: `${formData.desiredRole} candidate (${formData.minStipend})`,
        });
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : 'Could not save onboarding profile.');
        setSaving(false);
        return;
      }
      setSaving(false);
    }
    router.push('/overview');
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-white flex flex-col justify-center items-center px-4 py-12 relative">
      <div className="w-full max-w-2xl space-y-8 relative z-10">
        {/* Progress Bar & Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/25">
            <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
            <span>Collegiate Onboarding Wizard</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Create Your Career Passport</h1>
          <p className="text-xs text-slate-400">Step {step} of 5: Complete your verified academic profile.</p>

          {/* Stepper Dots */}
          <div className="flex items-center justify-center gap-2 pt-2">
            {[1, 2, 3, 4, 5].map((s) => (
              <div
                key={s}
                className={`h-2 rounded-full transition-all duration-300 ${
                  s === step
                    ? 'w-8 bg-cyan-400'
                    : s < step
                    ? 'w-4 bg-indigo-600'
                    : 'w-2 bg-slate-800'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Wizard Step Card */}
        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 sm:p-8 shadow-2xl backdrop-blur-md">
          {/* STEP 1: Indic Language Selection */}
          {step === 1 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
                <Globe className="h-4 w-4 text-cyan-400" />
                <span>Select Your Preferred Operating & Voice Language</span>
              </div>
              <p className="text-xs text-slate-400">
                NexteRaS adapts all opportunity matches, voice assistance, and ATS coaching to your chosen language.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    onClick={() => {
                      setFormData({ ...formData, preferredLanguage: lang.code as any });
                      setActiveLanguage(lang.code as any);
                    }}
                    className={`flex items-center justify-between p-3.5 rounded-xl border text-left transition ${
                      formData.preferredLanguage === lang.code
                        ? 'border-cyan-500 bg-cyan-950/40 text-white ring-1 ring-cyan-500'
                        : 'border-slate-800 bg-slate-900/40 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="text-sm font-bold">{lang.name}</div>
                      <div className="text-xs text-slate-400">{lang.native}</div>
                    </div>
                    {formData.preferredLanguage === lang.code && <Check className="h-4 w-4 text-cyan-400" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 2: Academic Profile */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
                <GraduationCap className="h-4 w-4 text-cyan-400" />
                <span>Academic & College Credentials</span>
              </div>

              <Input
                label="Full Name"
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                required
              />

              <Input
                label="College or University Name"
                value={formData.collegeName}
                onChange={(e) => setFormData({ ...formData, collegeName: e.target.value })}
                required
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select
                  label="Degree"
                  value={formData.degree}
                  onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                  options={[
                    { value: 'B.Tech', label: 'B.Tech / B.E.' },
                    { value: 'M.Tech', label: 'M.Tech / M.E.' },
                    { value: 'MCA', label: 'MCA' },
                    { value: 'B.Sc', label: 'B.Sc' },
                    { value: 'Ph.D', label: 'Ph.D' },
                  ]}
                />
                <Input
                  label="Branch / Major"
                  value={formData.branch}
                  onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                  placeholder="e.g. Computer Science"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select
                  label="Graduation Year"
                  value={formData.graduationYear.toString()}
                  onChange={(e) => setFormData({ ...formData, graduationYear: parseInt(e.target.value, 10) })}
                  options={[
                    { value: '2024', label: '2024 (Batch)' },
                    { value: '2025', label: '2025 (Graduating)' },
                    { value: '2026', label: '2026 (Pre-final)' },
                    { value: '2027', label: '2027 (Sophomore)' },
                    { value: '2028', label: '2028 (Freshman)' },
                  ]}
                />
                <Input
                  label="Current CGPA / Percentage"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  value={formData.cgpa.toString()}
                  onChange={(e) => setFormData({ ...formData, cgpa: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>
          )}

          {/* STEP 3: Skills & Domain Tags */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
                <Wrench className="h-4 w-4 text-cyan-400" />
                <span>Skills & Engineering Stack</span>
              </div>
              <p className="text-xs text-slate-400">
                Add programming languages, frameworks, and AI tools for automated opportunity matching.
              </p>

              <div className="flex gap-2">
                <Input
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  placeholder="e.g. PyTorch, React, Go, Docker"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                />
                <Button type="button" variant="secondary" size="md" onClick={addSkill}>
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 pt-2 min-h-20 p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
                {formData.skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-950 text-indigo-300 border border-indigo-700/60"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="text-slate-400 hover:text-white ml-1"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4: Career Preferences */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
                <Compass className="h-4 w-4 text-cyan-400" />
                <span>Opportunity & Stipend Preferences</span>
              </div>

              <Input
                label="Target Engineering Role"
                value={formData.desiredRole}
                onChange={(e) => setFormData({ ...formData, desiredRole: e.target.value })}
                placeholder="e.g. AI Research Intern or Full Stack Engineer"
              />

              <Input
                label="Preferred Location"
                value={formData.desiredLocation}
                onChange={(e) => setFormData({ ...formData, desiredLocation: e.target.value })}
                placeholder="e.g. Bangalore, Hyderabad, Remote"
              />

              <Input
                label="Minimum Stipend Expectation"
                value={formData.minStipend}
                onChange={(e) => setFormData({ ...formData, minStipend: e.target.value })}
                placeholder="e.g. ₹35,000 / month"
              />
            </div>
          )}

          {/* STEP 5: Review & Confirmation */}
          {step === 5 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
                <Award className="h-4 w-4 text-emerald-400" />
                <span>Ready to Generate Career Passport</span>
              </div>

              <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-white text-sm">{formData.fullName}</div>
                  <Badge variant="emerald">AICTE & UGC Linked</Badge>
                </div>
                <div className="text-xs text-slate-300 space-y-1">
                  <div>
                    {formData.degree} in {formData.branch} • {formData.collegeName}
                  </div>
                  <div>
                    Batch of {formData.graduationYear} • CGPA: {formData.cgpa}
                  </div>
                </div>

                <div className="pt-2 border-t border-emerald-800/40 flex flex-wrap gap-1.5">
                  {formData.skills.map((s) => (
                    <span key={s} className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-700">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed">
                By completing onboarding, your verified Career Passport ID will be persisted to PostgreSQL across all 9 regional languages.
              </p>
              {errorMsg && (
                <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 p-3 text-xs text-rose-200">
                  {errorMsg}
                </div>
              )}
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-800 mt-6">
            {step > 1 ? (
              <Button type="button" variant="outline" size="sm" onClick={() => setStep(step - 1)}>
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            ) : (
              <div />
            )}

            {step < 5 ? (
              <Button type="button" variant="primary" size="md" onClick={() => setStep(step + 1)}>
                <span>Next Step</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button type="button" variant="glow" size="md" isLoading={saving} onClick={() => void handleFinish()}>
                <Sparkles className="h-4 w-4 mr-1.5 text-cyan-300" />
                <span>Launch My Workspace</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
