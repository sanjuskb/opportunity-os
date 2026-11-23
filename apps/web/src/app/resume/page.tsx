'use client';

import React, { useState } from 'react';
import { FileText, Sparkles, CheckCircle2, Download, Copy, Check, AlertCircle, Wrench } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';

export default function ResumePage() {
  const { studentProfile } = useMockStore();
  const [copied, setCopied] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedAlert, setOptimizedAlert] = useState(false);

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(`# ${studentProfile.fullName}\n${studentProfile.headline}\n${studentProfile.email}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOptimizeBullets = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
      setOptimizedAlert(true);
      setTimeout(() => setOptimizedAlert(false), 3000);
    }, 1200);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header Strip */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">ATS Resume Studio</h1>
              <Badge variant="cyan">AI Optimization Engine</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Grounded resume analysis matching verified Indian internship rubrics and applicant tracking systems.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="outline" size="sm" onClick={handleCopyMarkdown}>
              {copied ? <Check className="h-4 w-4 mr-1 text-emerald-400" /> : <Copy className="h-4 w-4 mr-1" />}
              <span>{copied ? 'Copied Markdown' : 'Copy Text'}</span>
            </Button>
            <Button variant="glow" size="sm" onClick={handleOptimizeBullets} isLoading={isOptimizing}>
              <Sparkles className="h-4 w-4 mr-1.5" />
              <span>Tailor for Indian AI Roles</span>
            </Button>
          </div>
        </div>

        {optimizedAlert && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in duration-200">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>AI Resume Optimization Complete: Added verified quantitative metrics and Indic speech keywords. Match score increased to 96%!</span>
          </div>
        )}

        {/* ATS Score & Diagnostic Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-5 flex items-center gap-4 bg-gradient-to-br from-[#0D1322] to-[#0B0F19]">
            <div className="h-16 w-16 rounded-2xl bg-cyan-950 border border-cyan-500/40 flex items-center justify-center font-black text-2xl text-cyan-400 shadow-lg shadow-cyan-500/10">
              {studentProfile.atsScore}%
            </div>
            <div>
              <div className="text-xs uppercase font-bold text-slate-400 tracking-wider">ATS Score</div>
              <div className="text-sm font-bold text-white">Top 5% Candidate</div>
              <div className="text-[11px] text-emerald-400 font-medium">Parseable & Grounded</div>
            </div>
          </Card>

          <Card className="p-5 space-y-1">
            <span className="text-xs text-slate-400">Action Verbs & Impact</span>
            <div className="text-xl font-bold text-emerald-400">18 Quantified Metrics</div>
            <p className="text-[11px] text-slate-400">Latency, throughput, and accuracy metrics present.</p>
          </Card>

          <Card className="p-5 space-y-1">
            <span className="text-xs text-slate-400">Keyword Density</span>
            <div className="text-xl font-bold text-cyan-400">92% Match</div>
            <p className="text-[11px] text-slate-400">Matches PyTorch, Next.js, and Indic LLM rubrics.</p>
          </Card>

          <Card className="p-5 space-y-1">
            <span className="text-xs text-slate-400">Formatting Check</span>
            <div className="text-xl font-bold text-white">Standard Single-Col</div>
            <p className="text-[11px] text-slate-400">Zero multi-column table parsing bugs.</p>
          </Card>
        </div>

        {/* Split Screen Editor / Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Resume Content Inspector */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Grounded Resume Sections</CardTitle>
              <Badge variant="slate">Verified via DigiLocker</Badge>
            </CardHeader>
            <CardContent className="space-y-6 text-xs text-slate-200">
              {/* Education */}
              <div className="space-y-1.5 pb-4 border-b border-slate-800">
                <span className="font-bold text-sm text-cyan-400 uppercase tracking-wider">Education</span>
                <div className="font-bold text-white">{studentProfile.collegeName}</div>
                <div className="text-slate-400">
                  {studentProfile.degree} in {studentProfile.branch} (Batch of {studentProfile.graduationYear})
                </div>
                <div className="text-emerald-400 font-semibold">Current CGPA: {studentProfile.cgpa} / 10.0</div>
              </div>

              {/* Skills */}
              <div className="space-y-1.5 pb-4 border-b border-slate-800">
                <span className="font-bold text-sm text-cyan-400 uppercase tracking-wider">Technical Skills</span>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {studentProfile.skills.map((sk) => (
                    <span key={sk} className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-200 border border-slate-700">
                      {sk}
                    </span>
                  ))}
                </div>
              </div>

              {/* Projects */}
              <div className="space-y-3 pb-2">
                <span className="font-bold text-sm text-cyan-400 uppercase tracking-wider">Key Projects</span>
                {studentProfile.projects.map((p) => (
                  <div key={p.title} className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] space-y-1">
                    <div className="font-bold text-white">{p.title}</div>
                    <p className="text-slate-300 leading-relaxed text-[11px]">{p.description}</p>
                    <div className="text-[10px] text-cyan-400 font-mono pt-1">
                      Tech: {p.technologies.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Right: AI Bullet Optimizer Suggestions */}
          <Card className="border-indigo-500/25 bg-gradient-to-b from-[#0D1322] to-[#0B0F19]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-cyan-400" />
                <span>AI Bullet Point Enhancer</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2">
                <div className="text-[10px] uppercase font-bold text-amber-400">Original Bullet Point:</div>
                <p className="text-slate-400 italic">&quot;Worked on Indic speech models for Indian regional languages.&quot;</p>
                <div className="text-[10px] uppercase font-bold text-emerald-400 pt-1">AI Quantified Optimization:</div>
                <p className="text-slate-200 font-medium">
                  &quot;Fine-tuned multilingual Conformer acoustic models on Common Voice Telugu and Tamil datasets, reducing Word Error Rate (WER) by 14.2% under edge deployment constraints.&quot;
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2">
                <div className="text-[10px] uppercase font-bold text-amber-400">Original Bullet Point:</div>
                <p className="text-slate-400 italic">&quot;Built the frontend for Opportunity OS using Next.js.&quot;</p>
                <div className="text-[10px] uppercase font-bold text-emerald-400 pt-1">AI Quantified Optimization:</div>
                <p className="text-slate-200 font-medium">
                  &quot;Engineered an accessible React Three Fiber 3D architectural campus and responsive Tailwind UI across 7 native Indic languages, achieving sub-120ms interaction latency.&quot;
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-indigo-500/20 bg-indigo-950/20 text-indigo-300 space-y-1">
                <div className="font-bold">ATS Recruiter Insight:</div>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  Indian hiring managers at top tech firms (Google BLR, Zerodha, Postman) prioritize verifiable metric improvements and open-source commit history.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
