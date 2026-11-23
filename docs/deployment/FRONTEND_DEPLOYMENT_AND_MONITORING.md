# Opportunity OS — Frontend Deployment, Environment & Observability

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Frontend Deployment, Hosting, Environment Variables & Observability  
**Owner:** Sanju (Frontend & ML Lead)  
**Infrastructure Partner:** Ramaraju (Backend & Deployment Lead)  
**Implementation Target:** `apps/web/Dockerfile`, Vercel Configuration & Sentry  

---

## 1. Hosting Architecture & Strategy

Opportunity OS frontend (`@opportunity-os/web`) is built with Next.js 15 using the App Router. To ensure zero downtime, rapid CDN asset delivery across India, and predictable container portability during the Homingo Hackathon, two production deployment options are defined.

### 1.1 Deployment Strategy Comparison

| Strategy | Recommended Use Case | Hosting Platform | Edge Caching & Routing | DevOps Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **Strategy A (Primary)** | Production & Cloud Demo | **Vercel** | Global Edge Network (Mumbai / Chennai PoPs) | Zero DevOps; instant git preview deploys |
| **Strategy B (Self-Hosted)** | Local Evaluation / Hackathon Submission | **Docker (Standalone)** | Self-hosted Linux VM / Docker Compose | Minimal; runs `node server.js` |

---

## 2. Next.js 15 Standalone Docker Deployment

The repository includes a production-hardened, multi-stage Dockerfile configured specifically for Next.js 15 standalone output (`output: 'standalone'` in `apps/web/next.config.ts`).

### 2.1 Multi-Stage Build Topology
1. **Stage 1 (`deps`):** Installs production and build dependencies with pnpm.
2. **Stage 2 (`builder`):** Compiles Next.js standalone server and optimized client bundles.
3. **Stage 3 (`runner`):** Minimal Alpine Linux runtime container executing as an unprivileged non-root user (`nodejs:nextjs` UID 1001).

```dockerfile
# apps/web/Dockerfile
FROM node:20-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

FROM base AS deps
WORKDIR /app
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared-types/package.json ./packages/shared-types/
COPY packages/shared-config/package.json ./packages/shared-config/
COPY packages/design-tokens/package.json ./packages/design-tokens/
COPY packages/api-client/package.json ./packages/api-client/
RUN pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN pnpm --filter @opportunity-os/shared-types build
RUN pnpm --filter @opportunity-os/api-client build
RUN pnpm --filter @opportunity-os/web build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "apps/web/server.js"]
```

---

## 3. Environment Variable Governance & Matrix

Environment variables are partitioned strictly into **Public Client Variables** (prefixed with `NEXT_PUBLIC_` and embedded into the client JS bundle at build time) and **Server-Only Variables** (accessed exclusively on the Node.js server).

### 3.1 Environment Variable Matrix

| Variable Name | Scope | Description | Sample / Production Value |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_APP_URL` | Public (Client) | Canonical public URL of the web application | `https://opportunityos.in` |
| `NEXT_PUBLIC_API_URL` | Public (Client) | Base URL for FastAPI REST endpoints | `https://api.opportunityos.in/api/v1` |
| `NEXT_PUBLIC_WS_VOICE_URL` | Public (Client) | WebSocket URL for low-latency voice streaming | `wss://api.opportunityos.in/api/v1/voice/stream` |
| `NEXT_PUBLIC_SUPABASE_URL` | Public (Client) | Supabase project API gateway | `https://xyzproject.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public (Client) | Public client anonymous Supabase key | `eyJhbGciOiJIUzI1Ni...` |
| `NEXT_PUBLIC_DEFAULT_LOCALE` | Public (Client) | Default fallback locale code | `en` |
| `NEXT_PUBLIC_SENTRY_DSN` | Public (Client) | Sentry error reporting ingest endpoint | `https://abc@o123.ingest.sentry.io/456` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Server Only** | Administrative key for server-side operations | *Never expose to client* |
| `SENTRY_AUTH_TOKEN` | **Build Only** | Token used by CI to upload release source maps | *CI secret only* |

---

## 4. Observability, Telemetry & Real User Monitoring (RUM)

### 4.1 Error Tracking with Sentry
- **Client & Server Integration:** `@sentry/nextjs` captures uncaught runtime exceptions, React component render crashes, and unhandled Promise rejections.
- **Privacy Redaction:** To ensure compliance with student data privacy:
  - Form field inputs (`fullName`, `email`, `phone`, `password`) are automatically scrubbed.
  - Audio chunk byte streams are **never captured in error breadcrumbs**.
  - User identifiers are hashed before transmission.

### 4.2 Web Vitals Telemetry
Opportunity OS tracks real-world client performance across Indian mobile networks using the standard Next.js Web Vitals reporter:

```typescript
// apps/web/src/app/reportWebVitals.ts
export function reportWebVitals(metric: any) {
  if (process.env.NODE_ENV !== 'production') return;

  const body = JSON.stringify({
    name: metric.name,     // LCP, INP, CLS, TTFB
    value: metric.value,   // Metric duration / shift score
    rating: metric.rating, // 'good' | 'needs-improvement' | 'poor'
    delta: metric.delta,
    id: metric.id,
    page: window.location.pathname,
  });

  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/telemetry/vitals', body);
  }
}
```

### 4.3 Voice Telemetry Metrics
Voice interactions report the following operational metrics to assess pipeline health:
- `time_to_first_audio_byte_ms`: Latency between student end-of-speech and first audible response chunk.
- `voice_session_duration_sec`: Total duration of conversational session.
- `interruption_count`: Number of times the student interrupted AI speech.
- `fallback_to_text_count`: Frequency of microphone or socket errors triggering text mode.
