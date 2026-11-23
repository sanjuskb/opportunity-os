'use client';

import React, { useState } from 'react';
import { Video, Mic, Sparkles, CheckCircle2, Play, RotateCcw, Volume2, Shield } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';

export default function InterviewPage() {
  const { activeLanguage } = useMockStore();
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [feedbackReady, setFeedbackReady] = useState(false);

  const questions = [
    {
      role: 'Indic Speech & NLP Engineer',
      question:
        'Explain how Conformer acoustic architectures differ from standard Transformers when processing regional Indian speech with high dialect variance.',
      idealPoints: [
        'Macaron-style feed-forward modules flanking multi-head self-attention',
        'Depthwise convolution layers capturing local phonetic context',
        'Relative positional embeddings accommodating variable utterance length',
      ],
      aiFeedback:
        'Excellent technical depth! You accurately highlighted depthwise convolutions for local acoustic structure and relative positional embeddings. Communication score: 94/100.',
    },
    {
      role: 'Full Stack & Voice Systems',
      question:
        'How do you handle real-time WebAudio streaming over WebSockets while preventing buffer overflow and audio frame dropping on constrained 4G networks?',
      idealPoints: [
        'AudioWorklet processing off the main UI thread',
        'PCM chunk buffering with backpressure signaling',
        'Adaptive bitrate downsampling during network jitter',
      ],
      aiFeedback:
        'Great emphasis on offloading to AudioWorklet! Adding mention of Opus codec compression would make your answer outstanding. Score: 91/100.',
    },
  ];

  const currentQ = questions[activeQuestionIdx];

  const handleSimulateAnswer = () => {
    setIsRecording(true);
    setFeedbackReady(false);
    setTimeout(() => {
      setIsRecording(false);
      setFeedbackReady(true);
    }, 2000);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">AI Interview Simulator</h1>
              <Badge variant="violet">Gemini Voice Room</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Practice real technical interview questions tailored to Indian tech firms with real-time feedback.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActiveQuestionIdx((prev) => (prev + 1) % questions.length);
                setFeedbackReady(false);
              }}
            >
              <span>Next Question</span>
            </Button>
          </div>
        </div>

        {/* Video / Audio Room Canvas */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Question & Simulation Console (2 Cols) */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-slate-800 bg-[#0B0F19]">
              <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Target Role: {currentQ.role}
                  </span>
                </div>
                <Badge variant="cyan">Question {activeQuestionIdx + 1} of 2</Badge>
              </CardHeader>

              <CardContent className="p-6 space-y-6">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                  <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Technical Question:</div>
                  <p className="text-base font-bold text-white leading-relaxed">{currentQ.question}</p>
                </div>

                {/* Simulated Audio Response Controls */}
                <div className="flex flex-col items-center justify-center p-8 rounded-2xl border border-slate-800 bg-[#070B14] text-center space-y-4">
                  <div className="relative">
                    {isRecording && (
                      <div className="absolute -inset-3 rounded-full border-2 border-cyan-400 animate-ping opacity-40" />
                    )}
                    <button
                      type="button"
                      onClick={handleSimulateAnswer}
                      className={`h-20 w-20 rounded-full flex items-center justify-center shadow-xl transition active:scale-95 ${
                        isRecording
                          ? 'bg-red-500 text-white animate-pulse'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-500/25'
                      }`}
                    >
                      <Mic className="h-8 w-8" />
                    </button>
                  </div>

                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      {isRecording ? 'Listening & Analyzing Speech...' : 'Tap Mic to Deliver Your Spoken Answer'}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">
                      Simulates microphone input via Web Audio API & AudioWorklet.
                    </p>
                  </div>
                </div>

                {/* AI Instant Feedback */}
                {feedbackReady && (
                  <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2 animate-in fade-in duration-300">
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-300">
                      <Sparkles className="h-4 w-4 text-emerald-400" />
                      <span>Gemini Evaluation Feedback</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">{currentQ.aiFeedback}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Key Answer Points & Rubric */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Ideal Response Rubric</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-300">
                <p className="text-slate-400">Indian technical interviewers evaluate clarity, architectural grounding, and:</p>
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
                  <span>Multilingual Voice Support</span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  Practice answering in English, Telugu, Hindi, or Tamil. The AI will translate and evaluate core technical concepts accurately.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
