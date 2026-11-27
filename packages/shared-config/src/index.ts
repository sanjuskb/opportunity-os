export const APP_CONFIG = {
  APP_NAME: 'NexteRaS',
  APP_TAGLINE: 'The Upcoming Era.',
  APP_DESCRIPTION: 'An AI-powered career intelligence and autonomous employability system.',
  SUPPORTED_LANGUAGES: [
    { code: 'en', name: 'English', native: 'English' },
    { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
    { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', native: 'മലയാളം' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা' },
    { code: 'mr', name: 'Marathi', native: 'मराठी' },
    { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
  ],
  DEFAULT_LANGUAGE: 'en',
  MAX_RESUME_FILE_SIZE_MB: 5,
  PAGINATION_DEFAULT_LIMIT: 20,
} as const;
