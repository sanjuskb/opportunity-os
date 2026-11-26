/**
 * Canonical domain types for NexteRaS (Opportunity OS)
 */

export type IndianLanguage =
  | 'en'
  | 'hi'
  | 'te'
  | 'ta'
  | 'kn'
  | 'ml'
  | 'bn';

export type OpportunityType =
  | 'internship'
  | 'full_time'
  | 'scholarship'
  | 'hackathon'
  | 'fellowship'
  | 'government_scheme';

export type ApplicationStatus =
  | 'discovered'
  | 'saved'
  | 'evaluating'
  | 'eligible'
  | 'ineligible'
  | 'drafting'
  | 'ready_for_review'
  | 'approved'
  | 'submitted'
  | 'rejected'
  | 'accepted';

export interface UserProfile {
  userId: string;
  email: string;
  fullName?: string | null;
  avatarUrl?: string | null;
  preferredLanguage: string;
  supabaseRole: string;
}

export interface EducationItem {
  id: string;
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startYear: number;
  endYear?: number | null;
  score?: string | null;
}

export interface ApiStudentProfile {
  id: string;
  userId: string;
  collegeName: string;
  degree: string;
  branch: string;
  graduationYear: number;
  cgpa?: number | null;
  state?: string | null;
  bio?: string | null;
  currentAcademicYear?: number | null;
  activeBacklogs?: number;
  experienceMonths?: number;
  citizenship?: string | null;
  skills?: string[];
  preferredLocations?: string[];
  openToRelocate?: boolean;
  education: EducationItem[];
}

export interface StudentProfile {
  id: string;
  userId: string;
  fullName: string;
  email: string;
  phone?: string;
  collegeName: string;
  degree: string;
  branch: string;
  graduationYear: number;
  cgpa?: number;
  state: string;
  preferredLanguage: IndianLanguage;
  skills: string[];
  createdAt: string;
  updatedAt: string;
}

export interface StudentProfileUpsertPayload {
  collegeName: string;
  degree: string;
  branch: string;
  graduationYear: number;
  cgpa?: number | null;
  state?: string | null;
  bio?: string | null;
  currentAcademicYear?: number | null;
  activeBacklogs?: number | null;
  experienceMonths?: number | null;
  citizenship?: string | null;
  skills?: string[];
  preferredLocations?: string[];
  openToRelocate?: boolean;
}

export interface EducationCreatePayload {
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startYear: number;
  endYear?: number | null;
  score?: string | null;
}

export interface CareerPassport {
  id: string;
  studentId: string;
  verifiedAchievements: Array<Record<string, unknown>>;
  coursework: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  projects: Array<Record<string, unknown>>;
  lastUpdated?: string | null;
}

export interface Opportunity {
  id: string;
  title: string;
  organization: string;
  location: string;
  type: OpportunityType;
  description: string;
  stipendOrSalary?: string;
  deadline?: string;
  sourceUrl: string;
  sourceProvider: 'olostep' | 'crustdata' | 'manual' | 'direct_portal';
  retrievalTimestamp: string;
  requiredSkills: string[];
  eligibleBatches: number[];
  eligibleDegrees: string[];
  minCgpa?: number;
}

export interface ApiOpportunity {
  id: string;
  title: string;
  organization: string;
  location: string;
  type: string;
  description: string;
  stipendOrSalary?: string | null;
  deadline?: string | null;
  sourceUrl: string;
  sourceProvider: string;
  retrievalTimestamp?: string | null;
  isActive: boolean;
  requiredSkills: string[];
  eligibleBatches: number[];
  eligibleDegrees: string[];
  eligibleBranches: string[];
  eligibleAcademicYears?: number[];
  minCgpa?: number | null;
  maxActiveBacklogs?: number | null;
  minExperienceMonths?: number | null;
  allowedLocations?: string[];
  remoteAllowed?: boolean;
  requiredCitizenship?: string | null;
  preferredSkills?: string[];
  matchScore?: number | null;
  semanticScore?: number | null;
  isEligible?: boolean | null;
  matchReasons?: string[];
  matchedSkills?: string[];
  missingSkills?: string[];
}

export interface PaginatedOpportunities {
  items: ApiOpportunity[];
  nextCursor?: string | null;
  hasMore: boolean;
}

export interface EligibilityResult {
  opportunityId: string;
  isEligible: boolean;
  score: number; // 0 to 100
  deterministicChecks: {
    batchMatched: boolean;
    degreeMatched: boolean;
    cgpaMatched: boolean;
  };
  skillOverlap: {
    matchedSkills: string[];
    missingSkills: string[];
  };
  explanation: string;
}

export interface ApiEligibilityResult {
  opportunityId: string;
  studentId: string;
  isEligible: boolean;
  score: number;
  reasons: string[];
  missingSkills: string[];
  deterministicChecks?: {
    batchMatched: boolean;
    degreeMatched: boolean;
    cgpaMatched: boolean;
  };
  skillOverlap?: {
    matchedSkills: string[];
    missingSkills: string[];
  };
  explanation?: string;
}

export interface ApplicationRecord {
  id: string;
  userId: string;
  opportunityId: string;
  status: string;
  appliedAt?: string | null;
  submissionMethod: string;
  createdAt?: string | null;
}

export interface ApprovalRequest {
  id: string;
  sessionId: string;
  userId: string;
  opportunityId: string;
  actionType: string;
  payloadSummary: Record<string, unknown>;
  status: string;
  userDecisionAt?: string | null;
  rejectionReason?: string | null;
  createdAt?: string | null;
}

export interface ApprovalDecisionResult {
  approvalId: string;
  userId: string;
  opportunityId: string;
  status: string;
  userDecisionAt?: string | null;
}

export interface NotificationItem {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: string;
  isRead: boolean;
  createdAt?: string | null;
}

export interface ResumeRecord {
  id: string;
  userId: string;
  title: string;
  masterContent: Record<string, unknown>;
  storageBucket?: string | null;
  storagePath?: string | null;
  originalFilename?: string | null;
  mimeType?: string | null;
  fileSizeBytes?: number | null;
  fileSha256?: string | null;
  extractionStatus?: string | null;
  extractionConfidence?: number | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ResumeAnalyzeResult {
  resumeId: string;
  opportunityId?: string | null;
  completenessScore: number;
  extractedSkills: string[];
  matchedSkills: string[];
  missingSkills: string[];
  warnings: string[];
  recommendations: string[];
}

export interface ResumeCustomizationResult {
  id: string;
  resumeId: string;
  opportunityId: string;
  versionNumber: number;
  alignmentScore: number;
  tailoredContent: Record<string, unknown>;
  verifiedClaims: Array<Record<string, unknown>>;
  rejectedClaims: Array<Record<string, unknown>>;
  createdAt?: string | null;
}

export interface VoiceTicket {
  ticket: string;
  expiresAt: string;
  ttlSeconds: number;
}

export interface VoiceSessionRecord {
  id: string;
  userId: string;
  detectedLanguage: string;
  audioDurationSeconds: number;
  transcript?: string | null;
  status: string;
  createdAt?: string | null;
}

export interface OrganizationRecord {
  id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  headcountRange?: string | null;
  fundingStage?: string | null;
  description?: string | null;
  hiringVelocityScore?: number | null;
  isVerified: boolean;
  lastEnrichedAt?: string | null;
}

export interface WatchtowerMonitor {
  id: string;
  userId: string;
  targetOrganization: string;
  criteria: Record<string, unknown>;
  isActive: boolean;
  createdAt?: string | null;
}

export interface MlHealthStatus {
  status: string;
  readiness: string;
  device: string;
  cuda_available: boolean;
  loaded_models: string[];
  registry_count: number;
  ml_available: boolean;
  details: Record<string, unknown>;
}
