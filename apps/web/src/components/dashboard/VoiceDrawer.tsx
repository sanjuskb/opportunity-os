'use client';

import React, { useEffect, useRef, useState } from 'react';
import { X, Mic, MicOff, Sparkles, Globe, ArrowRight, Send } from 'lucide-react';
import Link from 'next/link';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { useAuth } from '../auth/AuthProvider';
import { getMessages } from '../../lib/i18n/messages';
import { AudioStreamingService } from '../../lib/voice/audioStreamer';

const DEMO_VOICE_QUERIES: Record<
  string,
  { query: string; response: string; actionText: string; actionLink: string }
> = {
  en: {
    query: 'Show me AI research internships in Bangalore with stipend above 40k.',
    response: 'Top matches: AI4Bharat (IIT Madras) ₹45,000/mo and Google India ₹1,20,000/mo.',
    actionText: 'View Opportunities',
    actionLink: '/opportunities',
  },
  hi: {
    query: 'मुझे बैंगलोर में 40 हज़ार से ज़्यादा स्टाइपेंड वाली एआई इंटर्नशिप दिखाएं।',
    response: 'आपके लिए शीर्ष अवसर: AI4Bharat ₹45,000/माह और Google India ₹1,20,000/माह।',
    actionText: 'अवसर देखें',
    actionLink: '/opportunities',
  },
  te: {
    query: 'బెంగళూరులో 40 వేల కంటే ఎక్కువ స్టైపెండ్ ఉన్న ఏఐ ఇంటర్న్‌షిప్‌లు చూపించండి.',
    response: 'మీ ప్రొఫైల్‌కు సరిపోయే అవకాశాలు: AI4Bharat మరియు Google India.',
    actionText: 'అవకాశాలు చూడండి',
    actionLink: '/opportunities',
  },
  ta: {
    query: 'பெங்களூரில் 40k க்கும் அதிகமான உதவித்தொகையுடன் கூடிய AI இன்டர்ன்ஷிப்களைக் காட்டு.',
    response: 'உங்கள் தகுதிக்கு ஏற்ற வாய்ப்புகள்: AI4Bharat மற்றும் Google India.',
    actionText: 'வாய்ப்புகளைப் பார்க்கவும்',
    actionLink: '/opportunities',
  },
  kn: {
    query: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ 40 ಸಾವಿರಕ್ಕಿಂತ ಹೆಚ್ಚು ಸ್ಟೈಫಂಡ್ ಇರುವ ಎಐ ಇಂಟರ್ನ್‌ಶಿಪ್‌ಗಳನ್ನು ತೋರಿಸಿ.',
    response: 'ನಿಮ್ಮ ಪ್ರೊಫైಲ್‌ಗೆ ಹೊಂದಿಕೆಯಾಗುವ ಅವಕಾಶಗಳು: AI4Bharat ಮತ್ತು Google India.',
    actionText: 'ಅವಕಾಶಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
    actionLink: '/opportunities',
  },
  ml: {
    query: 'ബാംഗ്ലൂരിൽ 40k-ൽ കൂടുതൽ സ്റ്റൈപ്പൻഡുള്ള AI ഇന്റേൺഷിപ്പുകൾ കാണിക്കുക.',
    response: 'നിങ്ങൾക്കായി കണ്ടെത്തിയ ഇന്റേൺഷിപ്പുകൾ: AI4Bharat, Google India.',
    actionText: 'അവസരങ്ങൾ കാണുക',
    actionLink: '/opportunities',
  },
  bn: {
    query: 'বেঙ্গালুরুতে ৪০ হাজারের বেশি স্টাইপেন্ড সহ এআই ইন্টার্নশিপ দেখান।',
    response: 'আপনার জন্য শীর্ষ সুযোগ: AI4Bharat এবং Google India.',
    actionText: 'সুযোগগুলি দেখুন',
    actionLink: '/opportunities',
  },
  mr: {
    query: 'मला बेंगळुरूमध्ये ४० हजारांपेक्षा जास्त स्टायपेंड असलेली AI इंटर्नशिप दाखवा.',
    response: 'तुमच्यासाठी योग्य संधी: AI4Bharat आणि Google India.',
    actionText: 'संधी पहा',
    actionLink: '/opportunities',
  },
  gu: {
    query: 'બેંગ્લોરમાં ૪૦ હજારથી વધુ સ્ટાઇપેન્ડ ધરાવતી AI ઇન્ટર્નશિપ બતાવો.',
    response: 'તમારી પ્રોફાઇલ માટે શ્રેષ્ઠ તકો: AI4Bharat અને Google India.',
    actionText: 'તકો જુઓ',
    actionLink: '/opportunities',
  },
};

function buildVoiceWsUrl(ticket: string): string {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';
  if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
    const wsBase = apiBase.replace(/^http/, 'ws').replace(/\/$/, '');
    return `${wsBase}/voice/stream?ticket=${encodeURIComponent(ticket)}`;
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${apiBase.replace(/\/$/, '')}/voice/stream?ticket=${encodeURIComponent(ticket)}`;
}

export function VoiceDrawer() {
  const { user, apiClient } = useAuth();
  const {
    isVoiceAssistantOpen,
    setIsVoiceAssistantOpen,
    isVoiceListening,
    setIsVoiceListening,
    activeLanguage,
    setActiveLanguage,
  } = useMockStore();

  const [streamStatus, setStreamStatus] = useState<'idle' | 'connecting' | 'live' | 'fallback' | 'closed' | 'error'>('idle');
  const [currentText, setCurrentText] = useState<string>('');
  const [currentAiResponse, setCurrentAiResponse] = useState<string>('');
  const [textInput, setTextInput] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const streamerRef = useRef<AudioStreamingService | null>(null);

  useEffect(() => {
    return () => {
      streamerRef.current?.disconnect();
      streamerRef.current = null;
    };
  }, []);

  if (!isVoiceAssistantOpen) return null;

  const localized = getMessages(activeLanguage);
  const currentScenario = DEMO_VOICE_QUERIES[activeLanguage] || DEMO_VOICE_QUERIES.en;
  const activeLangObj = APP_CONFIG.SUPPORTED_LANGUAGES.find((l) => l.code === activeLanguage);

  const startVoiceSession = async () => {
    if (isVoiceListening) {
      streamerRef.current?.stopMicrophone();
      setIsVoiceListening(false);
      if (user && currentText) {
        try {
          await apiClient.createVoiceSession({
            detectedLanguage: activeLanguage,
            audioDurationSeconds: 5,
            transcript: `${currentText}\n${currentAiResponse}`.trim(),
            status: 'completed',
          });
        } catch {
          // Session log persistence should not interrupt user
        }
      }
      return;
    }

    setStatusError(null);
    setCurrentAiResponse('');

    if (!user) {
      setIsVoiceListening(true);
      setCurrentText(`"${currentScenario.query}"`);
      window.setTimeout(() => {
        setIsVoiceListening(false);
        setCurrentAiResponse(currentScenario.response);
      }, 600);
      return;
    }

    try {
      setStreamStatus('connecting');
      const ticketRes = await apiClient.issueVoiceTicket();
      const wsUrl = buildVoiceWsUrl(ticketRes.ticket);
      const streamer = new AudioStreamingService({
        onStatusChange: (nextStatus) => setStreamStatus(nextStatus),
        onUserTranscript: (text) => setCurrentText((prev) => `${prev} ${text}`.trim()),
        onAiTranscript: (text) => setCurrentAiResponse((prev) => `${prev} ${text}`.trim()),
        onError: (msg) => setStatusError(msg),
      });
      streamerRef.current?.disconnect();
      streamerRef.current = streamer;
      await streamer.connect(wsUrl, activeLanguage);
      await streamer.startMicrophone();
      setIsVoiceListening(true);
    } catch (err) {
      setIsVoiceListening(false);
      setStreamStatus('fallback');
      setStatusError(err instanceof Error ? err.message : 'Microphone unavailable; use text input below.');
    }
  };

  const handleSendTextQuery = async (queryText: string) => {
    const trimmed = queryText.trim();
    if (!trimmed || busy) return;
    setCurrentText(trimmed);
    setTextInput('');
    setStatusError(null);

    if (!user) {
      setCurrentAiResponse(currentScenario.response);
      return;
    }

    setBusy(true);
    try {
      const res = await apiClient.chatWithAssistant({
        message: trimmed,
        language: activeLanguage,
        conversationId,
      });
      setConversationId(res.conversationId);
      setCurrentAiResponse(res.reply);
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : 'Could not reach Career Copilot.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-[#090D16]/95 border-l border-slate-800 p-6 backdrop-blur-xl shadow-2xl flex flex-col justify-between animate-in slide-in-from-right duration-300">
      <div className="overflow-y-auto pr-1">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600/20 border border-violet-500/40 shadow-sm">
              <Sparkles className="h-4 w-4 text-violet-400" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">{localized.copilotTitle}</h2>
              <p className="text-[11px] text-slate-400">
                {streamStatus === 'live' ? localized.modeLive : localized.copilotSubtitle}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              streamerRef.current?.disconnect();
              setIsVoiceListening(false);
              setIsVoiceAssistantOpen(false);
            }}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close voice assistant"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="pt-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Globe className="h-3.5 w-3.5 text-cyan-400" />
              <span>Spoken Language:</span>
            </span>
            <span className="font-semibold text-cyan-300">
              {activeLangObj?.name} ({activeLangObj?.native})
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => {
                  setActiveLanguage(lang.code as typeof activeLanguage);
                  setCurrentText('');
                  setCurrentAiResponse('');
                }}
                className={`px-2 py-1 rounded text-[11px] font-medium border transition ${
                  activeLanguage === lang.code
                    ? 'bg-violet-950/80 text-violet-300 border-violet-500/60 shadow-sm ring-1 ring-violet-500/30'
                    : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-white'
                }`}
              >
                {lang.name}
              </button>
            ))}
          </div>
        </div>

        <div className="my-6 flex flex-col items-center justify-center p-6 rounded-2xl border border-slate-800 bg-[#0B0F19] text-center space-y-4">
          <div className="relative flex items-center justify-center">
            {isVoiceListening && (
              <>
                <div className="absolute h-28 w-28 rounded-full border-2 border-cyan-400/30 animate-ping" />
                <div className="absolute h-36 w-36 rounded-full border border-violet-500/20 animate-pulse" />
              </>
            )}

            <button
              type="button"
              onClick={startVoiceSession}
              aria-label={isVoiceListening ? 'Stop Microphone' : 'Start Microphone'}
              className={`relative z-10 flex h-20 w-20 items-center justify-center rounded-full border shadow-xl transition active:scale-95 ${
                isVoiceListening
                  ? 'bg-cyan-500 border-cyan-300 text-black shadow-cyan-500/30'
                  : 'bg-gradient-to-r from-violet-600 to-indigo-600 border-violet-400/40 text-white hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/20'
              }`}
            >
              {isVoiceListening ? <MicOff className="h-8 w-8 animate-pulse" /> : <Mic className="h-8 w-8" />}
            </button>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {isVoiceListening ? localized.listening : localized.tapMicrophone}
            </div>
            <p className="text-xs text-slate-300 max-w-xs">{localized.greeting}</p>
          </div>
        </div>

        {statusError && (
          <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-2 text-[11px] text-amber-200">
            {statusError}
          </div>
        )}

        {(currentText || currentAiResponse) && (
          <div className="space-y-3 mb-4">
            {currentText && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-xs space-y-1">
                <div className="text-[10px] uppercase font-bold text-cyan-400">
                  Student ({activeLangObj?.name}):
                </div>
                <p className="text-slate-200">{currentText}</p>
              </div>
            )}

            {currentAiResponse && (
              <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3 text-xs space-y-2">
                <div className="text-[10px] uppercase font-bold text-violet-300 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                  <span>NexteRaS Intelligence:</span>
                </div>
                <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{currentAiResponse}</p>
                <div className="pt-1">
                  <Link
                    href={currentScenario.actionLink}
                    onClick={() => setIsVoiceAssistantOpen(false)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
                  >
                    <span>{localized.sampleAction}</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-slate-800/80 space-y-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void handleSendTextQuery(textInput);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={localized.sendMessagePlaceholder}
            className="flex-1 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:border-violet-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={busy || !textInput.trim()}
            className="inline-flex items-center gap-1 rounded-lg bg-violet-600 px-3 py-2 text-xs font-semibold text-white hover:bg-violet-500 disabled:opacity-50"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>

        <div>
          <div className="text-[11px] text-slate-400 mb-1">{localized.quickPromptLabel}</div>
          <button
            type="button"
            onClick={() => void handleSendTextQuery(localized.sampleQuery)}
            className="w-full text-left p-2 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-300 hover:border-slate-700 hover:text-white transition flex items-center justify-between"
          >
            <span className="truncate pr-2">&quot;{localized.sampleQuery}&quot;</span>
            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-500" />
          </button>
        </div>
      </div>
    </div>
  );
}
