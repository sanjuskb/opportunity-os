import test from 'node:test';
import assert from 'node:assert';
import { colors, materials3D } from '@opportunity-os/design-tokens';
import { APP_CONFIG } from '@opportunity-os/shared-config';

test('Ecosystem colour mapping adheres to Concept 4 + Concept 1 directive', () => {
  assert.strictEqual(colors.ecosystem.students, '#06B6D4', 'Students must be Cyan');
  assert.strictEqual(colors.ecosystem.companies, '#3B82F6', 'Companies must be Sapphire');
  assert.strictEqual(colors.ecosystem.universities, '#10B981', 'Universities must be Emerald');
  assert.strictEqual(colors.ecosystem.opportunities, '#F59E0B', 'Opportunities must be Amber');
  assert.strictEqual(colors.ecosystem.aiCore, '#8B5CF6', 'AI Core must be Violet');
});

test('3D Architectural Maquette materials are properly defined', () => {
  assert.strictEqual(materials3D.baseplate, '#0B0F19', 'Baseplate must be dark obsidian');
  assert.strictEqual(materials3D.titanium, '#94A3B8', 'Titanium must be satin metallic');
  assert.strictEqual(materials3D.slateStructure, '#1E293B', 'Slate must be dark architectural slate');
  assert.ok(materials3D.glass.includes('rgba'), 'Glass must have transparency');
  assert.strictEqual(materials3D.emissivePath, '#38BDF8', 'Pathways must be emissive cyan');
});

test('Product brand identity matches official NexteRaS configuration', () => {
  assert.strictEqual(APP_CONFIG.APP_NAME, 'NexteRaS', 'Official product name must be NexteRaS');
  assert.strictEqual(APP_CONFIG.APP_TAGLINE, 'The Upcoming Era.', 'Official tagline must match');
});

test('Supported languages configuration supports 7 Indian regional languages', () => {
  const codes = APP_CONFIG.SUPPORTED_LANGUAGES.map((l) => l.code);
  assert.strictEqual(codes.length, 7, 'Must support exactly 7 languages');
  assert.ok(codes.includes('en'), 'Must include English');
  assert.ok(codes.includes('hi'), 'Must include Hindi');
  assert.ok(codes.includes('te'), 'Must include Telugu');
  assert.ok(codes.includes('ta'), 'Must include Tamil');
  assert.ok(codes.includes('kn'), 'Must include Kannada');
  assert.ok(codes.includes('ml'), 'Must include Malayalam');
  assert.ok(codes.includes('bn'), 'Must include Bengali');
});
