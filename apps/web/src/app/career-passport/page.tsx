'use client';

import React, { useState } from 'react';
import { Award, ShieldCheck, Copy, Check, Plus } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useAddCareerPassportItem,
  useCareerPassport,
  useStudentProfile,
  useUserProfile,
} from '@/lib/queries/useOpportunityOs';

export default function CareerPassportPage() {
  const { user } = useAuth();
  const { data: userProfile } = useUserProfile();
  const { data: studentProfile } = useStudentProfile();
  const { data: passport, isLoading, error } = useCareerPassport();
  const addItem = useAddCareerPassportItem();

  const [copied, setCopied] = useState(false);
  const [category, setCategory] = useState<'projects' | 'certifications' | 'coursework' | 'verified_achievements'>('projects');
  const [itemTitle, setItemTitle] = useState('');
  const [itemDetail, setItemDetail] = useState('');
  const [formMsg, setFormMsg] = useState<string | null>(null);

  const handleCopyShareLink = () => {
    const id = passport?.id || 'draft';
    void navigator.clipboard.writeText(`${window.location.origin}/career-passport?id=${id}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemTitle.trim()) return;
    setFormMsg(null);
    try {
      await addItem.mutateAsync({
        category,
        item: {
          title: itemTitle.trim(),
          description: itemDetail.trim() || itemTitle.trim(),
          verifiedSource: 'student_submitted',
          addedAt: new Date().toISOString(),
        },
      });
      setItemTitle('');
      setItemDetail('');
      setFormMsg('Added record to Verified Career Passport.');
    } catch (err) {
      setFormMsg(err instanceof Error ? err.message : 'Unable to add item.');
    }
  };

  const displayName = userProfile?.fullName || user?.email?.split('@')[0] || 'Student';
  const totalCredentials =
    (passport?.certifications?.length ?? 0) +
    (passport?.verifiedAchievements?.length ?? 0) +
    (passport?.coursework?.length ?? 0);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Verified Career Passport</h1>
              <Badge variant="cyan">PostgreSQL Persisted</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Grounded academic records, certifications, coursework, and projects powering zero-hallucination resumes.
            </p>
          </div>

          <Button variant="outline" size="sm" onClick={handleCopyShareLink}>
            {copied ? <Check className="h-4 w-4 mr-1.5 text-emerald-400" /> : <Copy className="h-4 w-4 mr-1.5" />}
            <span>{copied ? 'Copied Link' : 'Share Passport'}</span>
          </Button>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200">
            Complete Onboarding to initialize your Student Profile &amp; Career Passport.
          </div>
        )}

        {isLoading ? (
          <div className="h-48 rounded-2xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : (
          <>
            <div className="rounded-2xl border-2 border-cyan-500/30 bg-gradient-to-br from-[#0B132B] via-[#090D16] to-[#070B14] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                <Award className="h-64 w-64 text-cyan-400" />
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10 pb-6 border-b border-slate-800/80">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 p-0.5 shadow-xl">
                    <div className="h-full w-full rounded-2xl bg-[#090D16] flex items-center justify-center font-black text-2xl text-cyan-300">
                      {displayName.charAt(0).toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <h2 className="text-xl sm:text-2xl font-black text-white">{displayName}</h2>
                    <p className="text-xs sm:text-sm text-cyan-300 font-medium">
                      {studentProfile?.bio || 'Engineering Candidate'}
                    </p>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {studentProfile?.collegeName || 'Set your college in Onboarding'} • Batch of{' '}
                      {studentProfile?.graduationYear || 2027}
                    </div>
                  </div>
                </div>

                <div className="text-left sm:text-right space-y-1">
                  <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Passport UUID:</div>
                  <div className="font-mono text-xs font-bold text-cyan-400 bg-slate-900/80 px-3 py-1 rounded-lg border border-slate-800">
                    {passport?.id || 'Pending setup'}
                  </div>
                  <div className="text-[11px] text-emerald-400 flex items-center gap-1 justify-start sm:justify-end">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>RLS Protected Record</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 relative z-10 text-xs">
                <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
                  <span className="text-slate-400">Cumulative CGPA</span>
                  <div className="text-lg font-bold text-white mt-1">
                    {studentProfile?.cgpa != null ? `${studentProfile.cgpa} / 10.0` : '—'}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
                  <span className="text-slate-400">Degree &amp; Branch</span>
                  <div className="text-lg font-bold text-white mt-1 truncate">
                    {studentProfile ? `${studentProfile.degree} ${studentProfile.branch}` : '—'}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
                  <span className="text-slate-400">Projects</span>
                  <div className="text-lg font-bold text-cyan-400 mt-1">{passport?.projects?.length ?? 0}</div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
                  <span className="text-slate-400">Credentials &amp; Coursework</span>
                  <div className="text-lg font-bold text-emerald-400 mt-1">{totalCredentials}</div>
                </div>
              </div>
            </div>

            {user && (
              <Card>
                <CardContent className="p-5 space-y-3">
                  <div className="text-sm font-bold text-white flex items-center gap-2">
                    <Plus className="h-4 w-4 text-cyan-400" />
                    <span>Add Grounded Record to Career Passport</span>
                  </div>
                  {formMsg && <p className="text-xs text-cyan-300">{formMsg}</p>}
                  <form onSubmit={handleAddItem} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value as typeof category)}
                      className="h-10 rounded-lg border border-slate-800 bg-slate-900 px-3 text-xs text-slate-200"
                    >
                      <option value="projects">Project</option>
                      <option value="certifications">Certification</option>
                      <option value="coursework">Coursework</option>
                      <option value="verified_achievements">Achievement</option>
                    </select>
                    <Input
                      value={itemTitle}
                      onChange={(e) => setItemTitle(e.target.value)}
                      placeholder="Title (e.g. FastAPI Distributed Queue)"
                      required
                    />
                    <Input
                      value={itemDetail}
                      onChange={(e) => setItemDetail(e.target.value)}
                      placeholder="Short evidence/tech details"
                    />
                    <Button type="submit" variant="primary" size="md" isLoading={addItem.isPending}>
                      Save Record
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { label: 'Projects', items: passport?.projects ?? [] },
                { label: 'Certifications', items: passport?.certifications ?? [] },
                { label: 'Coursework', items: passport?.coursework ?? [] },
                { label: 'Verified Achievements', items: passport?.verifiedAchievements ?? [] },
              ].map((section) => (
                <Card key={section.label}>
                  <CardContent className="p-5 space-y-3">
                    <h3 className="text-sm font-bold text-white">{section.label}</h3>
                    {section.items.length === 0 ? (
                      <p className="text-xs text-slate-500">No items added yet.</p>
                    ) : (
                      section.items.map((item, idx) => (
                        <div key={idx} className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] text-xs space-y-1">
                          <div className="font-bold text-white">
                            {String((item as Record<string, unknown>).title || 'Passport Item')}
                          </div>
                          <p className="text-slate-300">
                            {String((item as Record<string, unknown>).description || '')}
                          </p>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
