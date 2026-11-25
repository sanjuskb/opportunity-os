'use client';

import React, { useState } from 'react';
import { X, Mic, MicOff, Sparkles, Volume2, Globe, ArrowRight } from 'lucide-react';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import Link from 'next/link';

const DEMO_VOICE_QUERIES: Record<
  string,
  { query: string; nativeQuery: string; response: string; nativeResponse: string; actionText: string; actionLink: string }
> = {
  en: {
    query: 'Show me AI research internships in Bangalore with stipend above 40k.',
    nativeQuery: 'Show me AI research internships in Bangalore with stipend above 40k.',
    response: 'I found 2 top opportunities matching your criteria: AI4Bharat (IIT Madras) offering ₹45,000/mo and Google India offering ₹1,20,000/mo. Your ATS match is 94%.',
    nativeResponse: 'I found 2 top opportunities matching your criteria: AI4Bharat (IIT Madras) offering ₹45,000/mo and Google India offering ₹1,20,000/mo.',
    actionText: 'View AI4Bharat Internship',
    actionLink: '/opportunities',
  },
  hi: {
    query: 'मुझे बैंगलोर में 40 हज़ार से ज़्यादा स्टाइपेंड वाली एआई इंटर्नशिप दिखाएं।',
    nativeQuery: 'मुझे बैंगलोर में 40 हज़ार से ज़्यादा स्टाइपेंड वाली एआई इंटर्नशिप दिखाएं।',
    response: 'मुझे आपके लिए 2 सबसे अच्छी इंटर्नशिप मिली हैं: AI4Bharat (IIT मद्रास) ₹45,000/माह और Google India ₹1,20,000/माह। आपकी योग्यता 94% मेल खाती है।',
    nativeResponse: 'मुझे आपके लिए 2 सबसे अच्छी इंटर्नशिप मिली हैं: AI4Bharat और Google India.',
    actionText: 'अवसर देखें',
    actionLink: '/opportunities',
  },
  te: {
    query: 'బెంగళూరులో 40 వేల కంటే ఎక్కువ స్టైపెండ్ ఉన్న ఏఐ ఇంటర్న్‌షిప్‌లు చూపించండి.',
    nativeQuery: 'బెంగళూరులో 40 వేల కంటే ఎక్కువ స్టైపెండ్ ఉన్న ఏఐ ఇంటర్న్‌షిప్‌లు చూపించండి.',
    response: 'మీ ప్రొఫైల్‌కు సరిపోయే 2 అద్భుతమైన అవకాశాలు దొరికాయి: AI4Bharat (IIT మద్రాస్) ₹45,000/నెల మరియు Google India ₹1,20,000/నెల. మీ అర్హత స్కోరు 94%.',
    nativeResponse: 'AI4Bharat మరియు Google India లో మీకు తగిన ఇంటర్న్‌షిప్‌లు ఉన్నాయి.',
    actionText: 'అవకాశాలు చూడండి',
    actionLink: '/opportunities',
  },
  ta: {
    query: 'பெங்களூரில் 40k க்கும் அதிகமான உதவித்தொகையுடன் கூடிய AI இன்டர்ன்ஷிப்களைக் காட்டு.',
    nativeQuery: 'பெங்களூரில் 40k க்கும் அதிகமான உதவித்தொகையுடன் கூடிய AI இன்டர்ன்ஷிப்களைக் காட்டு.',
    response: 'உங்கள் தகுதிக்கு ஏற்ற 2 வாய்ப்புகள் உள்ளன: AI4Bharat ₹45,000/மாதம் மற்றும் Google India ₹1,20,000/மாதம்.',
    nativeResponse: 'AI4Bharat மற்றும் Google India நிறுவனங்களில் உங்களுக்கு வாய்ப்புகள் உள்ளன.',
    actionText: 'வாய்ப்புகளைப் பார்க்கவும்',
    actionLink: '/opportunities',
  },
  kn: {
    query: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ 40 ಸಾವಿರಕ್ಕಿಂತ ಹೆಚ್ಚು ಸ್ಟೈಫಂಡ್ ಇರುವ ಎಐ ಇಂಟರ್ನ್‌ಶಿಪ್‌ಗಳನ್ನು ತೋರಿಸಿ.',
    nativeQuery: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ 40 ಸಾವಿರಕ್ಕಿಂತ ಹೆಚ್ಚು ಸ್ಟೈಫಂಡ್ ಇರುವ ಎಐ ಇಂಟರ್ನ್‌ಶಿಪ್‌ಗಳನ್ನು ತೋರಿಸಿ.',
    response: 'ನಿಮ್ಮ ಪ್ರೊಫೈಲ್‌ಗೆ ಹೊಂದಿಕೆಯಾಗುವ 2 ಅವಕಾಶಗಳು ಲಭ್ಯವಿವೆ: AI4Bharat ಮತ್ತು Google India.',
    nativeResponse: 'AI4Bharat ಮತ್ತು Google India ಇಂಟರ್ನ್‌ಶಿಪ್‌ಗಳು.',
    actionText: 'ಅವಕಾಶಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
    actionLink: '/opportunities',
  },
  ml: {
    query: 'ബാംഗ്ലൂരിൽ 40k-ൽ കൂടുതൽ സ്റ്റൈപ്പൻഡുള്ള AI ഇന്റേൺഷിപ്പുകൾ കാണിക്കുക.',
    nativeQuery: 'ബാംഗ്ലൂരിൽ 40k-ൽ കൂടുതൽ സ്റ്റൈപ്പൻഡുള്ള AI ഇന്റേൺഷിപ്പുകൾ കാണിക്കുക.',
    response: 'നിങ്ങൾക്കായി 2 മികച്ച ഇന്റേൺഷിപ്പുകൾ കണ്ടെത്തി: AI4Bharat, Google India.',
    nativeResponse: 'AI4Bharat, Google India അവസരങ്ങൾ.',
    actionText: 'അവസരങ്ങൾ കാണുക',
    actionLink: '/opportunities',
  },
  bn: {
    query: 'বেঙ্গালুরুতে ৪০ হাজারের বেশি স্টাইপেন্ড সহ এআই ইন্টার্নশিপ দেখান।',
    nativeQuery: 'বেঙ্গালুরুতে ৪০ হাজারের বেশি স্টাইপেন্ড সহ এআই ইন্টার্নশিপ দেখান।',
    response: 'আপনার জন্য ২টি শীর্ষ সুযোগ পাওয়া গেছে: AI4Bharat এবং Google India.',
    nativeResponse: 'AI4Bharat এবং Google India ইন্টার্নশিপ পাওয়া গেছে।',
    actionText: 'সুযোগগুলি দেখুন',
    actionLink: '/opportunities',
  },
};

export function VoiceDrawer() {
  const {
    isVoiceAssistantOpen,
    setIsVoiceAssistantOpen,
    isVoiceListening,
    setIsVoiceListening,
    activeLanguage,
    setActiveLanguage,
  } = useMockStore();

  const [activeVoiceSession, setActiveVoiceSession] = useState(false);
  const [currentText, setCurrentText] = useState<string>('');
  const [currentAiResponse, setCurrentAiResponse] = useState<string>('');

  if (!isVoiceAssistantOpen) return null;

  const currentScenario = DEMO_VOICE_QUERIES[activeLanguage] || DEMO_VOICE_QUERIES.en;
  const activeLangObj = APP_CONFIG.SUPPORTED_LANGUAGES.find((l) => l.code === activeLanguage);

  const startListeningSimulation = () => {
    setIsVoiceListening(true);
    setActiveVoiceSession(true);
    setCurrentText('Listening to Indian speech audio...');
    setCurrentAiResponse('');

    setTimeout(() => {
      setCurrentText(`"${currentScenario.query}"`);
      setIsVoiceListening(false);

      setTimeout(() => {
        setCurrentAiResponse(currentScenario.response);
      }, 700);
    }, 1800);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-[#090D16]/95 border-l border-slate-800 p-6 backdrop-blur-xl shadow-2xl flex flex-col justify-between animate-in slide-in-from-right duration-300">
      {/* Drawer Header */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600/20 border border-violet-500/40 shadow-sm">
              <Sparkles className="h-4 w-4 text-violet-400" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Indic Voice Copilot</h2>
              <p className="text-[11px] text-slate-400">14-State Acoustic Lifecycle Engine</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsVoiceAssistantOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close voice assistant"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Language Selection Strip */}
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
                onClick={() => {
                  setActiveLanguage(lang.code as any);
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

        {/* Central Audio Visualizer Simulation */}
        <div className="my-8 flex flex-col items-center justify-center p-6 rounded-2xl border border-slate-800 bg-[#0B0F19] text-center space-y-4">
          <div className="relative flex items-center justify-center">
            {/* Visualizer Pulses */}
            {isVoiceListening && (
              <>
                <div className="absolute h-28 w-28 rounded-full border-2 border-cyan-400/30 animate-ping" />
                <div className="absolute h-36 w-36 rounded-full border border-violet-500/20 animate-pulse" />
              </>
            )}

            <button
              type="button"
              onClick={startListeningSimulation}
              className={`relative z-10 flex h-20 w-20 items-center justify-center rounded-full border shadow-xl transition active:scale-95 ${
                isVoiceListening
                  ? 'bg-cyan-500 border-cyan-300 text-black shadow-cyan-500/30'
                  : 'bg-gradient-to-r from-violet-600 to-indigo-600 border-violet-400/40 text-white hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/20'
              }`}
            >
              {isVoiceListening ? <Mic className="h-8 w-8 animate-pulse" /> : <Mic className="h-8 w-8" />}
            </button>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {isVoiceListening ? 'Listening (Web Audio Stream)...' : 'Tap Microphone to Speak'}
            </div>
            <p className="text-xs text-slate-300 max-w-xs">
              Natural conversational interface supporting 7 Indian languages.
            </p>
          </div>
        </div>

        {/* Live Conversation Stream Box */}
        {activeVoiceSession && (
          <div className="space-y-3">
            {currentText && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-xs space-y-1">
                <div className="text-[10px] uppercase font-bold text-cyan-400 flex items-center gap-1">
                  <span>Student Query ({activeLangObj?.name}):</span>
                </div>
                <p className="text-slate-200 italic">{currentText}</p>
              </div>
            )}

            {currentAiResponse && (
              <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3 text-xs space-y-2 animate-in fade-in duration-300">
                <div className="text-[10px] uppercase font-bold text-violet-300 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                  <span>NexteRaS Intelligence:</span>
                </div>
                <p className="text-slate-200 leading-relaxed">{currentAiResponse}</p>
                <div className="pt-1">
                  <Link
                    href={currentScenario.actionLink}
                    onClick={() => setIsVoiceAssistantOpen(false)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
                  >
                    <span>{currentScenario.actionText}</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Drawer Footer with Quick-Prompt Suggestion */}
      <div className="pt-4 border-t border-slate-800/80 space-y-2">
        <div className="text-[11px] text-slate-400">Quick Prompt Suggestion:</div>
        <button
          type="button"
          onClick={() => {
            startListeningSimulation();
          }}
          className="w-full text-left p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-300 hover:border-slate-700 hover:text-white transition flex items-center justify-between"
        >
          <span className="truncate pr-2">&quot;{currentScenario.query}&quot;</span>
          <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-500" />
        </button>
      </div>
    </div>
  );
}
