'use client';

import React, { useState } from 'react';
import { FileText, Sparkles, CheckCircle2, Download, Upload, AlertCircle } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useAnalyzeResume,
  useOpportunities,
  useResumes,
  useTailorResume,
  useUploadResume,
} from '@/lib/queries/useOpportunityOs';
import type { ResumeAnalyzeResult, ResumeCustomizationResult } from '@opportunity-os/shared-types';

export default function ResumePage() {
  const { user, session, apiClient } = useAuth();
  const { data: resumes, isLoading } = useResumes();
  const { data: oppPage } = useOpportunities({ limit: 15 });
  const uploadMutation = useUploadResume();
  const analyzeMutation = useAnalyzeResume();
  const tailorMutation = useTailorResume();

  const [selectedOpportunityId, setSelectedOpportunityId] = useState('');
  const [analysis, setAnalysis] = useState<ResumeAnalyzeResult | null>(null);
  const [tailorRes, setTailorRes] = useState<ResumeCustomizationResult | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const activeResume = (resumes ?? [])[0] ?? null;
  const opportunities = oppPage?.items ?? [];

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      const uploaded = await uploadMutation.mutateAsync({ file, title: file.name, syncToProfile: true });
      setStatusMsg(`Uploaded & extracted "${uploaded.title}" cleanly.`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Resume upload failed.');
    }
  };

  const handleAnalyze = async () => {
    if (!activeResume) return;
    setErrorMsg(null);
    try {
      const res = await analyzeMutation.mutateAsync({
        resumeId: activeResume.id,
        opportunityId: selectedOpportunityId || undefined,
      });
      setAnalysis(res);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Resume analysis failed.');
    }
  };

  const handleTailor = async () => {
    if (!activeResume || !selectedOpportunityId) {
      setErrorMsg('Select a target opportunity to tailor your resume against.');
      return;
    }
    setErrorMsg(null);
    try {
      const res = await tailorMutation.mutateAsync({
        resumeId: activeResume.id,
        opportunityId: selectedOpportunityId,
      });
      setTailorRes(res);
      setStatusMsg(`Tailored resume v${res.versionNumber} with ${Math.round(res.alignmentScore)}% grounded alignment.`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Resume tailoring failed.');
    }
  };

  const handleDownloadPdf = async () => {
    if (!activeResume) return;
    setErrorMsg(null);
    try {
      const pdfUrl = apiClient.getResumePdfUrl(activeResume.id);
      const resp = await fetch(pdfUrl, {
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status} while generating ATS PDF`);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${activeResume.title || 'resume'}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'PDF download failed.');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">ATS Resume Studio</h1>
              <Badge variant="cyan">Zero-Hallucination NLI</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Upload PDF or DOCX resumes to private Storage, inspect ATS completeness, and tailor strictly from verified records.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <label className="cursor-pointer inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition">
              <Upload className="h-3.5 w-3.5 text-cyan-400" />
              <span>{uploadMutation.isPending ? 'Uploading...' : 'Upload PDF / DOCX'}</span>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,.json"
                className="hidden"
                disabled={!user || uploadMutation.isPending}
                onChange={handleFileChange}
              />
            </label>
            <Button
              variant="outline"
              size="sm"
              disabled={!activeResume}
              isLoading={analyzeMutation.isPending}
              onClick={() => void handleAnalyze()}
            >
              <FileText className="h-4 w-4 mr-1" />
              <span>Analyze ATS</span>
            </Button>
            <Button
              variant="glow"
              size="sm"
              disabled={!activeResume || !selectedOpportunityId}
              isLoading={tailorMutation.isPending}
              onClick={() => void handleTailor()}
            >
              <Sparkles className="h-4 w-4 mr-1.5" />
              <span>Tailor Grounded Resume</span>
            </Button>
            <Button variant="secondary" size="sm" disabled={!activeResume} onClick={() => void handleDownloadPdf()}>
              <Download className="h-4 w-4 mr-1" />
              <span>ATS PDF</span>
            </Button>
          </div>
        </div>

        {statusMsg && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{statusMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-200 text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {isLoading ? (
          <div className="h-40 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : !activeResume ? (
          <Card>
            <CardContent className="p-8 text-center space-y-2">
              <div className="text-sm font-bold text-white">No Resumes Uploaded Yet</div>
              <p className="text-xs text-slate-400">
                Upload a PDF or DOCX resume above to extract skills and unlock ATS tailoring.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>{activeResume.title}</CardTitle>
                <Badge variant="emerald">Active Master Resume</Badge>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="space-y-1">
                  <div className="text-slate-400 uppercase font-bold text-[10px]">Extracted Skills</div>
                  <div className="flex flex-wrap gap-1.5">
                    {((activeResume.masterContent?.skills as string[]) ?? []).map((sk) => (
                      <span key={sk} className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
                {activeResume.masterContent?.rawText ? (
                  <div className="space-y-1">
                    <div className="text-slate-400 uppercase font-bold text-[10px]">Extracted Text Preview</div>
                    <pre className="max-h-60 overflow-y-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-[#0B0F19] p-3 text-[11px] text-slate-300">
                      {String(activeResume.masterContent.rawText)}
                    </pre>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Target Opportunity &amp; NLI Grounding</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <select
                  value={selectedOpportunityId}
                  onChange={(e) => setSelectedOpportunityId(e.target.value)}
                  className="w-full h-10 rounded-lg border border-slate-800 bg-slate-900 px-3 text-xs text-slate-200"
                >
                  <option value="">Select opportunity for ATS gap check / tailoring...</option>
                  {opportunities.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.title} — {opp.organization}
                    </option>
                  ))}
                </select>

                {analysis && (
                  <div className="p-3.5 rounded-xl border border-cyan-500/30 bg-cyan-950/20 space-y-2">
                    <div className="font-bold text-cyan-300">
                      ATS Completeness: {Math.round(analysis.completenessScore)}%
                    </div>
                    <div>Matched: {analysis.matchedSkills.join(', ') || '—'}</div>
                    <div>Missing: {analysis.missingSkills.join(', ') || 'None'}</div>
                    {analysis.recommendations.map((rec, i) => (
                      <div key={i} className="text-slate-300">• {rec}</div>
                    ))}
                  </div>
                )}

                {tailorRes && (
                  <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
                    <div className="font-bold text-emerald-300">
                      Tailored Version #{tailorRes.versionNumber} • Alignment {Math.round(tailorRes.alignmentScore)}%
                    </div>
                    <div>Verified Claims Accepted: {tailorRes.verifiedClaims.length}</div>
                    <div>Unsupported Claims Rejected: {tailorRes.rejectedClaims.length}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
