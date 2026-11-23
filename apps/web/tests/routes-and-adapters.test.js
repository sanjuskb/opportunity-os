import test from 'node:test';
import assert from 'node:assert';
import { MOCK_OPPORTUNITIES, MOCK_ELIGIBILITY_CACHE } from '../src/lib/mock-data/opportunities.ts';
import { CURRENT_STUDENT, MOCK_CANDIDATES } from '../src/lib/mock-data/students.ts';
import { APP_CONFIG } from '@opportunity-os/shared-config';

test('Mock opportunities dataset is robust and adheres to Opportunity OS schema', () => {
  assert.ok(MOCK_OPPORTUNITIES.length >= 6, 'Must provide at least 6 ingested opportunities');

  for (const opp of MOCK_OPPORTUNITIES) {
    assert.ok(opp.id, 'Opportunity must have an ID');
    assert.ok(opp.title, 'Opportunity must have a title');
    assert.ok(opp.organization, 'Opportunity must have an organization');
    assert.ok(opp.location, 'Opportunity must have a location');
    assert.ok(opp.stipendOrSalary, 'Opportunity must have stipend/salary');
    assert.ok(Array.isArray(opp.requiredSkills) && opp.requiredSkills.length > 0, 'Must have required skills');
    assert.ok(Array.isArray(opp.eligibleBatches) && opp.eligibleBatches.length > 0, 'Must have eligible batches');
  }
});

test('Student Career Passport data adheres to AICTE / UGC verification standard', () => {
  assert.strictEqual(CURRENT_STUDENT.id, 'std-sanju-01');
  assert.ok(CURRENT_STUDENT.cgpa >= 8.0, 'Student CGPA must be verified');
  assert.ok(CURRENT_STUDENT.careerPassportId.startsWith('PASSPORT-'), 'Must have canonical passport ID');
  assert.ok(CURRENT_STUDENT.verifiedCredentials.length >= 3, 'Must have at least 3 verified credentials');

  const aicte = CURRENT_STUDENT.verifiedCredentials.find((c) => c.verificationSource === 'AICTE');
  assert.ok(aicte, 'Must have AICTE accreditation badge');
});

test('Mock candidate database provides pre-screened talent across colleges', () => {
  assert.ok(MOCK_CANDIDATES.length >= 3, 'Must provide at least 3 student profiles');
  const colleges = MOCK_CANDIDATES.map((c) => c.collegeName);
  assert.ok(colleges.some((c) => c.includes('NIT')), 'Must include NIT');
  assert.ok(colleges.some((c) => c.includes('IIIT')), 'Must include IIIT');
  assert.ok(colleges.some((c) => c.includes('IIT')), 'Must include IIT');
});

test('Explainable match breakdown provides deterministic pre-checks and skill overlap', () => {
  const match = MOCK_ELIGIBILITY_CACHE['opp-ai4bharat-01'];
  assert.ok(match, 'AI4Bharat match cache must exist');
  assert.strictEqual(match.isEligible, true);
  assert.ok(match.score >= 90, 'Score must be >= 90%');
  assert.strictEqual(match.deterministicChecks.batchMatched, true);
  assert.strictEqual(match.deterministicChecks.degreeMatched, true);
  assert.strictEqual(match.deterministicChecks.cgpaMatched, true);
  assert.ok(match.skillOverlap.matchedSkills.length > 0);
});
