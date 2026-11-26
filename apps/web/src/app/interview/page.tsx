'use client';

import React, { useState } from 'react';
import { Sparkles, CheckCircle2, Play, Volume2, Send } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS, useInterviewSessions } from '@/lib/queries/useOpportunityOs';
import { useQueryClient } from '@tanstack/react-query';
import type { InterviewSessionRecord } from '@opportunity-os/shared-types';

export default function InterviewPage() {
  const { user, apiClient } = useAuth();
  const { activeLanguage } = useMockStore();
  const qc = useQueryClient();
  const { data: sessions } = useInterviewSessions();

  const [targetRole, setTargetRole] = useState('AI & Backend Engineering Intern');
  const [activeSession, setActiveSession] = useState<InterviewSessionRecord | null>(null);
  const [questionIdx, setQuestionIdx] = useState(0);
  const [answerText, setAnswerText] = useState('');
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const currentSession = activeSession ?? (sessions ?? [])[0] ?? null;
  const currentQ = currentSession?.questions?.[questionIdx] ?? null;
  const latestFeedback = currentSession?.feedback?.find(
    (f) => Number((f as Record<string, unknown>).questionIndex) === questionIdx
  ) as Record<string, unknown> | undefined;

  const handleStartSession = async () => {
    if (!user) return;
    setErrorMsg(null);
    setBusy(true);
    try {
      const created = await apiClient.createInterviewSession({
        targetRole: targetRole.trim() || 'Software Engineering Intern',
        language: activeLanguage,
      });
      setActiveSession(created);
      setQuestionIdx(0);
      setAnswerText('');
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.interviewSessions });
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to start interview session.');
    } finally {
      setBusy(false);
    }
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !currentSession || !answerText.trim()) return;
    setErrorMsg(null);
    setBusy(true);
    try {
      const updated = await apiClient.submitInterviewResponse(currentSession.id, {
        questionIndex: questionIdx,
        answerText: answerText.trim(),
      });
      setActiveSession(updated);
      setAnswerText('');
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.interviewSessions });
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to evaluate answer.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">AI Interview Simulator</h1>
              <Badge variant="violet">9-Language Gemini Coaching</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Practice role-specific technical interviews in {activeLanguage.toUpperCase()} with grounded rubric scoring.
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-end">
            <div className="flex-1 w-full">
              <Input
                label="Target Internship / Job Role"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Python FastAPI Intern"
              />
            </div>
            <Button variant="glow" size="md" disabled={!user} isLoading={busy} onClick={() => void handleStartSession()}>
              <Play className="h-4 w-4 mr-1.5" />
              <span>Start Interview Session</span>
            </Button>
          </CardContent>
        </Card>

        {errorMsg && (
          <div className="p-3 rounded-xl border border-rose-500/40 bg-rose-950/30 text-xs text-rose-200">
            {errorMsg}
          </div>
        )}

        {currentSession && currentQ ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card className="border-slate-800 bg-[#0B0F19]">
                <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Role: {currentSession.targetRole}
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge variant="cyan">
                      Question {questionIdx + 1} of {currentSession.questions.length}
                    </Badge>
                    {currentSession.questions.length > 1 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setQuestionIdx((prev) => (prev + 1) % currentSession.questions.length)}
                      >
                        Next
                      </Button>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="p-6 space-y-5">
                  <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Technical Prompt:</div>
                    <p className="text-base font-bold text-white leading-relaxed">{currentQ.question}</p>
                  </div>

                  <form onSubmit={handleSubmitAnswer} className="space-y-3">
                    <textarea
                      rows={5}
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Type your structured answer in your preferred language or English..."
                      className="w-full rounded-xl border border-slate-800 bg-[#070B14] p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:border-violet-500 focus:outline-none"
                      required
                    />
                    <Button type="submit" variant="primary" size="md" disabled={!user} isLoading={busy}>
                      <Send className="h-3.5 w-3.5 mr-1.5" />
                      <span>Submit &amp; Evaluate Answer</span>
                    </Button>
                  </form>

                  {latestFeedback && (
                    <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-emerald-300">
                        <span className="flex items-center gap-1.5">
                          <Sparkles className="h-4 w-4 text-emerald-400" />
                          <span>Evaluation Feedback</span>
                        </span>
                        <span>Score: {String(latestFeedback.score)}/100</span>
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed">{String(latestFeedback.summary)}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Ideal Evaluation Rubric</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs text-slate-300">
                  <ul className="space-y-2">
                    {currentQ.idealPoints.map((pt) => (
                      <li key={pt} className="flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card className="border-violet-500/20 bg-violet-950/20">
                <CardContent className="p-4 space-y-2 text-xs text-violet-200">
                  <div className="font-bold flex items-center gap-1.5">
                    <Volume2 className="h-4 w-4 text-violet-400" />
                    <span>9-Language Support Active</span>
                  </div>
                  <p className="text-[11px] text-slate-300">
                    Session scores are persisted in PostgreSQL. Overall Score:{' '}
                    {currentSession.overallScore != null ? `${currentSession.overallScore}/100` : 'In progress'}.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="p-8 rounded-xl border border-slate-800 bg-[#0B0F19] text-center text-xs text-slate-400">
            Click &quot;Start Interview Session&quot; above to generate role-tailored interview questions.
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
