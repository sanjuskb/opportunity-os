export interface LocalizedUiStrings {
  greeting: string;
  copilotTitle: string;
  copilotSubtitle: string;
  tapMicrophone: string;
  listening: string;
  sendMessagePlaceholder: string;
  sendButton: string;
  quickPromptLabel: string;
  sampleQuery: string;
  sampleAction: string;
  modeLive: string;
  modeFallback: string;
}

export const I18N_MESSAGES: Record<string, LocalizedUiStrings> = {
  en: {
    greeting: 'Explore opportunities and practice interviews in 9 Indian languages.',
    copilotTitle: 'Indic Voice Copilot',
    copilotSubtitle: 'Gemini Live Audio + Grounded Tool Calling',
    tapMicrophone: 'Tap Microphone to Speak',
    listening: 'Streaming 16kHz PCM Audio...',
    sendMessagePlaceholder: 'Or type a career question in any language...',
    sendButton: 'Send',
    quickPromptLabel: 'Quick Prompt Suggestion:',
    sampleQuery: 'Show me AI research internships in Bangalore with stipend above 40k.',
    sampleAction: 'View Opportunities',
    modeLive: 'Gemini Live Connected',
    modeFallback: 'Text Copilot Fallback',
  },
  hi: {
    greeting: '9 भारतीय भाषाओं में अवसर खोजें और साक्षात्कार का अभ्यास करें।',
    copilotTitle: 'इंडिक वॉइस कोपायलट',
    copilotSubtitle: 'जेमिनी लाइव ऑडियो + टूल्स',
    tapMicrophone: 'बोलने के लिए माइक्रोफोन दबाएं',
    listening: '16kHz ऑडियो स्ट्रीम हो रहा है...',
    sendMessagePlaceholder: 'या किसी भी भाषा में प्रश्न लिखें...',
    sendButton: 'भेजें',
    quickPromptLabel: 'त्वरित सुझाव:',
    sampleQuery: 'मुझे बैंगलोर में 40 हज़ार से ज़्यादा स्टाइपेंड वाली एआई इंटर्नशिप दिखाएं।',
    sampleAction: 'अवसर देखें',
    modeLive: 'जेमिनी लाइव कनेक्टेड',
    modeFallback: 'टेक्स्ट कोपायलट मोड',
  },
  te: {
    greeting: '9 భారతీయ భాషలలో అవకాశాలను అన్వేషించండి మరియు ఇంటర్వ్యూ సాధన చేయండి.',
    copilotTitle: 'ఇండిక్ వాయిస్ కోపైలట్',
    copilotSubtitle: 'జెమిని లైవ్ ఆడియో + టూల్స్',
    tapMicrophone: 'మాట్లాడటానికి మైక్ నొక్కండి',
    listening: '16kHz ఆడియో స్ట్రీమ్ అవుతోంది...',
    sendMessagePlaceholder: 'లేదా మీ ప్రశ్నను టైప్ చేయండి...',
    sendButton: 'పంపండి',
    quickPromptLabel: 'త్వరిత సూచన:',
    sampleQuery: 'బెంగళూరులో 40 వేల కంటే ఎక్కువ స్టైపెండ్ ఉన్న ఏఐ ఇంటర్న్‌షిప్‌లు చూపించండి.',
    sampleAction: 'అవకాశాలు చూడండి',
    modeLive: 'జెమిని లైవ్ కనెక్ట్ అయింది',
    modeFallback: 'టెక్స్ట్ కోపైలట్ మోడ్',
  },
  ta: {
    greeting: '9 இந்திய மொழிகளில் வாய்ப்புகளைத் தேடி நேர்காணல் பயிற்சி பெறுங்கள்.',
    copilotTitle: 'இந்திக் குரல் உதவியாளர்',
    copilotSubtitle: 'ஜெமினி லைவ் ஆடியோ + கருவிகள்',
    tapMicrophone: 'பேச மைக்ரோஃபோனைத் தட்டவும்',
    listening: '16kHz ஆடியோ இணைப்பில் உள்ளது...',
    sendMessagePlaceholder: 'அல்லது உங்கள் கேள்வியை தட்டச்சு செய்யவும்...',
    sendButton: 'அனுப்பு',
    quickPromptLabel: 'விரைவு பரிந்துரை:',
    sampleQuery: 'பெங்களூரில் 40k க்கும் அதிகமான உதவித்தொகையுடன் கூடிய AI இன்டர்ன்ஷிப்களைக் காட்டு.',
    sampleAction: 'வாய்ப்புகளைப் பார்க்கவும்',
    modeLive: 'ஜெமினி லைவ் இணைக்கப்பட்டது',
    modeFallback: 'உரை உதவியாளர் நிலை',
  },
  kn: {
    greeting: '9 ಭಾರತೀಯ ಭಾಷೆಗಳಲ್ಲಿ ಅವಕಾಶಗಳನ್ನು ಹುಡುಕಿ ಮತ್ತು ಸಂದರ್ಶನ ಅಭ್ಯಾಸ ಮಾಡಿ.',
    copilotTitle: 'ಇಂಡಿಕ್ ವಾಯ್ಸ್ ಕೋಪೈಲಟ್',
    copilotSubtitle: 'ಜೆಮಿನಿ ಲೈವ್ ಆಡಿಯೋ + ಟೂಲ್ಸ್',
    tapMicrophone: 'ಮಾತನಾಡಲು ಮೈಕ್ ಒತ್ತಿರಿ',
    listening: '16kHz ಆಡಿಯೋ ಸ್ಟ್ರೀಮ್ ಆಗುತ್ತಿದೆ...',
    sendMessagePlaceholder: 'ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...',
    sendButton: 'ಕಳುಹಿಸಿ',
    quickPromptLabel: 'ತ್ವರಿತ ಸಲಹೆ:',
    sampleQuery: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ 40 ಸಾವಿರಕ್ಕಿಂತ ಹೆಚ್ಚು ಸ್ಟೈಫಂಡ್ ಇರುವ ಎಐ ಇಂಟರ್ನ್‌ಶಿಪ್‌ಗಳನ್ನು ತೋರಿಸಿ.',
    sampleAction: 'ಅವಕಾಶಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
    modeLive: 'ಜೆಮಿನಿ ಲೈವ್ ಸಂಪರ್ಕಗೊಂಡಿದೆ',
    modeFallback: 'ಪಠ್ಯ ಕೋಪೈಲಟ್ ಮೋಡ್',
  },
  ml: {
    greeting: '9 ഇന്ത്യൻ ഭാഷകളിൽ അവസരങ്ങൾ കണ്ടെത്തുകയും അഭിമുഖം പരിശീലിക്കുകയും ചെയ്യുക.',
    copilotTitle: 'ഇൻഡിക് വോയിസ് കോപൈലറ്റ്',
    copilotSubtitle: 'ജെമിനി ലൈവ് ഓഡിയോ + ടൂളുകൾ',
    tapMicrophone: 'സംസാരിക്കാൻ മൈക്ക് ടാപ്പ് ചെയ്യുക',
    listening: '16kHz ഓഡിയോ സ്ട്രീം ചെയ്യുന്നു...',
    sendMessagePlaceholder: 'അല്ലെങ്കിൽ ചോദ്യം ടൈപ്പ് ചെയ്യുക...',
    sendButton: 'അയയ്ക്കുക',
    quickPromptLabel: 'പെട്ടെന്നുള്ള നിർദ്ദേശം:',
    sampleQuery: 'ബാംഗ്ലൂരിൽ 40k-ൽ കൂടുതൽ സ്റ്റൈപ്പൻഡുള്ള AI ഇന്റേൺഷിപ്പുകൾ കാണിക്കുക.',
    sampleAction: 'അവസരങ്ങൾ കാണുക',
    modeLive: 'ജെമിനി ലൈവ് കണക്റ്റ് ചെയ്തു',
    modeFallback: 'ടെക്സ്റ്റ് കോപൈലറ്റ് മോഡ്',
  },
  bn: {
    greeting: '৯টি ভারতীয় ভাষায় সুযোগ খুঁজুন এবং ইন্টারভিউ অনুশীলন করুন।',
    copilotTitle: 'ইন্ডিক ভয়েস কোপাইলট',
    copilotSubtitle: 'জেমিনি লাইভ অডিও + টুলস',
    tapMicrophone: 'কথা বলতে মাইকে ট্যাপ করুন',
    listening: '16kHz অডিও স্ট্রিম হচ্ছে...',
    sendMessagePlaceholder: 'অথবা আপনার প্রশ্ন লিখুন...',
    sendButton: 'পাঠান',
    quickPromptLabel: 'দ্রুত পরামর্শ:',
    sampleQuery: 'বেঙ্গালুরুতে ৪০ হাজারের বেশি স্টাইপেন্ড সহ এআই ইন্টার্নশিপ দেখান।',
    sampleAction: 'সুযোগগুলি দেখুন',
    modeLive: 'জেমিনি লাইভ সংযুক্ত',
    modeFallback: 'টেক্সট কোপাইলট মোড',
  },
  mr: {
    greeting: '९ भारतीय भाषांमध्ये संधी शोधा आणि मुलाखतीचा सराव करा.',
    copilotTitle: 'इंडिक व्हॉइस कोपायलट',
    copilotSubtitle: 'जेमिनी लाइव्ह ऑडिओ + टूल्स',
    tapMicrophone: 'बोलण्यासाठी माइकवर टॅप करा',
    listening: '16kHz ऑडिओ स्ट्रीम होत आहे...',
    sendMessagePlaceholder: 'किंवा तुमचा प्रश्न टाइप करा...',
    sendButton: 'पाठवा',
    quickPromptLabel: 'त्वरित सूचना:',
    sampleQuery: 'मला बेंगळुरूमध्ये ४० हजारांपेक्षा जास्त स्टायपेंड असलेली AI इंटर्नशिप दाखवा.',
    sampleAction: 'संधी पहा',
    modeLive: 'जेमिनी लाइव्ह कनेक्ट झाले',
    modeFallback: 'टेक्स्ट कोपायलट मोड',
  },
  gu: {
    greeting: '૯ ભારતીય ભાષાઓમાં તકો શોધો અને ઇન્ટરવ્યુની પ્રેક્ટિસ કરો.',
    copilotTitle: 'ઇન્ડિક વૉઇસ કોપાયલટ',
    copilotSubtitle: 'જેમિની લાઇવ ઑડિયો + ટૂલ્સ',
    tapMicrophone: 'બોલવા માટે માઇક પર ટૅપ કરો',
    listening: '16kHz ઑડિયો સ્ટ્રીમ થઈ રહ્યો છે...',
    sendMessagePlaceholder: 'અથવા તમારો પ્રશ્ન લખો...',
    sendButton: 'મોકલો',
    quickPromptLabel: 'ઝડપી સૂચન:',
    sampleQuery: 'બેંગ્લોરમાં ૪૦ હજારથી વધુ સ્ટાઇપેન્ડ ધરાવતી AI ઇન્ટર્નશિપ બતાવો.',
    sampleAction: 'તકો જુઓ',
    modeLive: 'જેમિની લાઇવ કનેક્ટેડ',
    modeFallback: 'ટેક્સ્ટ કોપાયલટ મોડ',
  },
};

export function getMessages(language: string): LocalizedUiStrings {
  return I18N_MESSAGES[language] || I18N_MESSAGES.en;
}
