# ADR-004: Multilingual Voice Engine Selection

## Status
Accepted

## Context
Target users are Indian undergraduate students across diverse states who often speak in Indic languages mixed with English (code-switching).

## Decision
Use Gemini Live Multilingual WebSocket API for low-latency bidirectional voice interaction across English, Hindi, Telugu, Tamil, Kannada, Malayalam, and Bengali, with graceful fallback to text chat.

## Consequences
- **Positive:** Native understanding of Indian accents and code-switching without needing separate ASR, translation, and TTS pipelines. Sub-second latency.
- **Negative:** Depends on high-quality internet connectivity on the client side; requires text fallback.
