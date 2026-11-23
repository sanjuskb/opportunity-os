# Opportunity OS — Security & Privacy Checklist

## 1. Identity, Authentication & Permissions

- [x] **No Hardcoded Secrets:** Zero API keys, JWT secrets, or DB passwords in source control (verified via pre-commit and automated checks).
- [x] **Safe Environment Template:** `.env.example` contains only variable names and safe placeholders.
- [ ] **Row-Level Security Enforcement:** Supabase RLS policies enabled and tested for all student tables (`profiles`, `resumes`, `applications`, `career_passports`).
- [ ] **JWT Signature Verification:** FastAPI verifies Supabase JWT signatures on all `/api/v1/*` routes except `/health`.

---

## 2. Data Privacy & Audio Governance

- [x] **Ephemeral Audio Streaming:** Student audio buffers processed in volatile memory; raw voice recordings are **never** written to database tables.
- [ ] **PII Redaction in Resumes:** Resumes stored in encrypted PostgreSQL columns; PII redacted before external telemetry logging.
- [x] **Source Provenance:** All scraped opportunity data retains source URLs and retrieval timestamps to prevent intellectual property misattribution.

---

## 3. Autonomous Execution & Ethical Guardrails

- [x] **Mandatory Human Approval Gate:** Playwright automation halts before final submission; requires student confirmation with visible dry-run screenshot and diff.
- [x] **Strict Anti-Bypass Policy:** The browser agent will **never** solve or bypass CAPTCHAs, Cloudflare Turnstile, or anti-bot defenses.
- [x] **No Plaintext Third-Party Passwords:** Application credentials for company portals are never requested or stored.
- [ ] **Rate Limiting & Abuse Prevention:** Redis-backed token bucket limits API queries per IP/user to prevent scraping abuse and API quota exhaustion.
