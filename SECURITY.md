# Security Policy

## Supported Versions
Only the latest baseline on `main` and `develop` is actively maintained.

## Reporting a Vulnerability
If you discover a security vulnerability or sensitive secret exposure:
1. Do NOT open a public GitHub issue.
2. Contact the core team directly at `sanju.skb.191144@gmail.com`.
3. Provide a description of the issue, affected components, and steps to reproduce.
4. The team will acknowledge receipt within 24 hours and patch the issue promptly.

## Sensitive Boundaries
- Never commit real API keys (Gemini, Olostep, Crustdata, Supabase).
- Browser automation must never bypass CAPTCHAs, bot defenses, or user authentication gates without human supervision.
