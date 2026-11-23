/**
 * Canonical domain types for Opportunity OS
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

export interface ApprovalRequest {
  id: string;
  sessionId: string;
  userId: string;
  opportunityId: string;
  actionType: 'form_submission' | 'email_outreach' | 'resume_dispatch';
  payloadSummary: Record<string, unknown>;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  resolvedAt?: string;
}
