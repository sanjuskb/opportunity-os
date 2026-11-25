import { create } from 'zustand';
import type { Opportunity, ApplicationStatus, IndianLanguage } from '@opportunity-os/shared-types';
import { MOCK_OPPORTUNITIES } from './opportunities';
import { CURRENT_STUDENT, MOCK_CANDIDATES, StudentFullData } from './students';

export type UserRole = 'student' | 'company' | 'university';

export interface AppliedRecord {
  id: string;
  opportunityId: string;
  status: ApplicationStatus;
  appliedAt: string;
  atsScore: number;
  stageNotes?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  type: 'match' | 'status' | 'verification' | 'system';
}

export interface MockStoreState {
  // Current Active Persona / Role
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;

  // Student Profile
  studentProfile: StudentFullData;
  updateStudentProfile: (updates: Partial<StudentFullData>) => void;

  // Opportunities
  opportunities: Opportunity[];
  savedOpportunityIds: string[];
  toggleSaveOpportunity: (id: string) => void;
  createOpportunity: (newOpp: Omit<Opportunity, 'id' | 'retrievalTimestamp'>) => void;

  // Applications
  applications: AppliedRecord[];
  applyToOpportunity: (opportunityId: string) => void;
  updateApplicationStatus: (appId: string, newStatus: ApplicationStatus) => void;

  // Candidates & Verification (Company & University)
  candidates: StudentFullData[];
  verifiedStudentIds: string[];
  verifyStudentCredential: (studentId: string) => void;

  // Notifications Tray
  notifications: NotificationItem[];
  markNotificationRead: (id: string) => void;
  clearAllNotifications: () => void;

  // Global Voice & Indic AI Assistant
  isVoiceAssistantOpen: boolean;
  setIsVoiceAssistantOpen: (open: boolean) => void;
  isVoiceListening: boolean;
  setIsVoiceListening: (listening: boolean) => void;
  voiceTranscript: string;
  setVoiceTranscript: (text: string) => void;
  voiceAiResponse: string;
  setVoiceAiResponse: (text: string) => void;
  activeLanguage: IndianLanguage;
  setActiveLanguage: (lang: IndianLanguage) => void;
}

export const useMockStore = create<MockStoreState>((set) => ({
  userRole: 'student',
  setUserRole: (role) => set({ userRole: role }),

  studentProfile: CURRENT_STUDENT,
  updateStudentProfile: (updates) =>
    set((state) => ({
      studentProfile: { ...state.studentProfile, ...updates },
    })),

  opportunities: MOCK_OPPORTUNITIES,
  savedOpportunityIds: ['opp-ai4bharat-01', 'opp-zerodha-03'],
  toggleSaveOpportunity: (id) =>
    set((state) => {
      const exists = state.savedOpportunityIds.includes(id);
      return {
        savedOpportunityIds: exists
          ? state.savedOpportunityIds.filter((item) => item !== id)
          : [...state.savedOpportunityIds, id],
      };
    }),

  createOpportunity: (newOpp) =>
    set((state) => {
      const created: Opportunity = {
        ...newOpp,
        id: `opp-custom-${Date.now()}`,
        retrievalTimestamp: new Date().toISOString(),
      };
      return {
        opportunities: [created, ...state.opportunities],
      };
    }),

  applications: [
    {
      id: 'app-01',
      opportunityId: 'opp-ai4bharat-01',
      status: 'submitted',
      appliedAt: '2026-11-20T10:30:00Z',
      atsScore: 94,
      stageNotes: 'Application verified by Career Passport and dispatched to AI4Bharat review committee.',
    },
    {
      id: 'app-02',
      opportunityId: 'opp-zerodha-03',
      status: 'ready_for_review',
      appliedAt: '2026-11-22T15:00:00Z',
      atsScore: 96,
      stageNotes: 'ATS resume customized. Student approval required before dispatch.',
    },
    {
      id: 'app-03',
      opportunityId: 'opp-google-blr-02',
      status: 'drafting',
      appliedAt: '2026-11-23T08:00:00Z',
      atsScore: 91,
      stageNotes: 'System design project bullet points undergoing AI optimization.',
    },
  ],

  applyToOpportunity: (opportunityId) =>
    set((state) => {
      const existing = state.applications.find((a) => a.opportunityId === opportunityId);
      if (existing) return state;

      const newRecord: AppliedRecord = {
        id: `app-${Date.now()}`,
        opportunityId,
        status: 'submitted',
        appliedAt: new Date().toISOString(),
        atsScore: 93,
        stageNotes: 'Application submitted with verified Career Passport credentials.',
      };

      const newNotification: NotificationItem = {
        id: `notif-${Date.now()}`,
        title: 'Application Dispatched',
        message: 'Your application has been verified and submitted with Career Passport.',
        timestamp: 'Just now',
        read: false,
        type: 'status',
      };

      return {
        applications: [newRecord, ...state.applications],
        notifications: [newNotification, ...state.notifications],
      };
    }),

  updateApplicationStatus: (appId, newStatus) =>
    set((state) => ({
      applications: state.applications.map((app) =>
        app.id === appId ? { ...app, status: newStatus } : app
      ),
    })),

  candidates: MOCK_CANDIDATES,
  verifiedStudentIds: ['std-sanju-01', 'std-ananya-02'],
  verifyStudentCredential: (studentId) =>
    set((state) => ({
      verifiedStudentIds: [...state.verifiedStudentIds, studentId],
      notifications: [
        {
          id: `notif-verify-${Date.now()}`,
          title: 'Institutional Verification Complete',
          message: `Degree and coursework verified for student ${studentId}.`,
          timestamp: 'Just now',
          read: false,
          type: 'verification',
        },
        ...state.notifications,
      ],
    })),

  notifications: [
    {
      id: 'notif-1',
      title: '94% Match Discovered',
      message: 'AI4Bharat has opened research internships matching your PyTorch and NLP profile.',
      timestamp: '2 hours ago',
      read: false,
      type: 'match',
    },
    {
      id: 'notif-2',
      title: 'Career Passport Verified',
      message: 'NIT Tiruchirappalli Registrar approved your 8.82 CGPA academic record via AICTE DigiLocker.',
      timestamp: '1 day ago',
      read: true,
      type: 'verification',
    },
    {
      id: 'notif-3',
      title: 'Application Review Pending',
      message: 'Zerodha Full Stack Fellow application is ready for your final approval.',
      timestamp: '2 days ago',
      read: true,
      type: 'status',
    },
  ],

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)),
    })),

  clearAllNotifications: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    })),

  // Voice AI
  isVoiceAssistantOpen: false,
  setIsVoiceAssistantOpen: (open) => set({ isVoiceAssistantOpen: open }),
  isVoiceListening: false,
  setIsVoiceListening: (listening) => set({ isVoiceListening: listening }),
  voiceTranscript: '',
  setVoiceTranscript: (text) => set({ voiceTranscript: text }),
  voiceAiResponse: '',
  setVoiceAiResponse: (text) => set({ voiceAiResponse: text }),
  activeLanguage: 'en',
  setActiveLanguage: (lang) => set({ activeLanguage: lang }),
}));
