'use client';

export interface VoiceStreamCallbacks {
  onStatusChange?: (status: 'idle' | 'connecting' | 'live' | 'fallback' | 'closed' | 'error') => void;
  onUserTranscript?: (text: string) => void;
  onAiTranscript?: (text: string) => void;
  onToolExecuted?: (toolName: string) => void;
  onError?: (message: string) => void;
}

/**
 * Bidirectional browser Web Audio + WebSocket PCM 16kHz/24kHz controller
 * connecting to FastAPI /api/v1/voice/stream with single-use ticket auth.
 */
export class AudioStreamingService {
  private ws: WebSocket | null = null;
  private mediaStream: MediaStream | null = null;
  private inputAudioContext: AudioContext | null = null;
  private playbackAudioContext: AudioContext | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private nextPlaybackTime = 0;
  private activeSources: AudioBufferSourceNode[] = [];
  private callbacks: VoiceStreamCallbacks;

  constructor(callbacks: VoiceStreamCallbacks = {}) {
    this.callbacks = callbacks;
  }

  async connect(wsUrl: string, language: string): Promise<boolean> {
    this.callbacks.onStatusChange?.('connecting');
    return new Promise((resolve) => {
      const socket = new WebSocket(wsUrl);
      socket.binaryType = 'arraybuffer';
      this.ws = socket;

      const timer = window.setTimeout(() => {
        if (socket.readyState !== WebSocket.OPEN) {
          socket.close();
          this.callbacks.onStatusChange?.('error');
          resolve(false);
        }
      }, 8000);

      socket.onopen = () => {
        window.clearTimeout(timer);
        socket.send(
          JSON.stringify({
            event: 'session_init',
            language,
            mode: 'live',
          })
        );
      };

      socket.onmessage = (event) => {
        if (typeof event.data !== 'string') return;
        try {
          const msg = JSON.parse(event.data) as Record<string, unknown>;
          const ev = String(msg.event || '');
          if (ev === 'live_connected') {
            this.callbacks.onStatusChange?.('live');
            resolve(true);
          } else if (ev === 'session_acknowledged') {
            // Wait briefly for live_connected; otherwise caller uses fallback or text_turn
            window.setTimeout(() => {
              if (this.ws?.readyState === WebSocket.OPEN) {
                this.callbacks.onStatusChange?.('fallback');
              }
              resolve(true);
            }, 600);
          } else if (ev === 'live_degraded') {
            this.callbacks.onStatusChange?.('fallback');
            resolve(true);
          } else if (ev === 'user_transcript' && typeof msg.text === 'string') {
            this.callbacks.onUserTranscript?.(msg.text);
          } else if (ev === 'ai_transcript' && typeof msg.text === 'string') {
            this.callbacks.onAiTranscript?.(msg.text);
          } else if (ev === 'tool_executed' && typeof msg.tool === 'string') {
            this.callbacks.onToolExecuted?.(msg.tool);
          } else if (ev === 'audio_delta' && typeof msg.data === 'string') {
            this.playBase64Pcm24k(msg.data);
          } else if (ev === 'playback_cancelled') {
            this.stopPlayback();
          }
        } catch {
          // Ignore non-JSON frames cleanly
        }
      };

      socket.onerror = () => {
        window.clearTimeout(timer);
        this.callbacks.onStatusChange?.('error');
        this.callbacks.onError?.('Voice WebSocket connection failed.');
        resolve(false);
      };

      socket.onclose = () => {
        this.stopMicrophone();
        this.callbacks.onStatusChange?.('closed');
      };
    });
  }

  async startMicrophone(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('Browser microphone API is unavailable.');
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });
    this.mediaStream = stream;

    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioCtx({ sampleRate: 16000 });
    this.inputAudioContext = ctx;
    const source = ctx.createMediaStreamSource(stream);
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    this.processorNode = processor;

    processor.onaudioprocess = (ev) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const input = ev.inputBuffer.getChannelData(0);
      const pcm = downsampleToPcm16(input, ctx.sampleRate, 16000);
      if (pcm.byteLength > 0) {
        this.ws.send(pcm.buffer);
      }
    };

    source.connect(processor);
    processor.connect(ctx.destination);
  }

  sendTextTurn(text: string, language: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.ws.send(
      JSON.stringify({
        event: 'text_turn',
        text,
        language,
      })
    );
  }

  interrupt(): void {
    this.stopPlayback();
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event: 'interrupted' }));
    }
  }

  stopMicrophone(): void {
    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }
    if (this.mediaStream) {
      for (const track of this.mediaStream.getTracks()) {
        track.stop();
      }
      this.mediaStream = null;
    }
    if (this.inputAudioContext) {
      void this.inputAudioContext.close();
      this.inputAudioContext = null;
    }
  }

  disconnect(): void {
    this.stopMicrophone();
    this.stopPlayback();
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      this.ws.close();
    }
    this.ws = null;
  }

  private stopPlayback(): void {
    for (const src of this.activeSources) {
      try {
        src.stop();
      } catch {
        // Ignore already-stopped nodes
      }
    }
    this.activeSources = [];
    this.nextPlaybackTime = 0;
  }

  private playBase64Pcm24k(b64: string): void {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!this.playbackAudioContext) {
        this.playbackAudioContext = new AudioCtx({ sampleRate: 24000 });
      }
      const ctx = this.playbackAudioContext;
      const binary = window.atob(b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const int16 = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
      }
      const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
      audioBuffer.copyToChannel(float32, 0);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      const startAt = Math.max(ctx.currentTime, this.nextPlaybackTime);
      source.start(startAt);
      this.nextPlaybackTime = startAt + audioBuffer.duration;
      this.activeSources.push(source);
      source.onended = () => {
        this.activeSources = this.activeSources.filter((s) => s !== source);
      };
    } catch {
      // Audio playback errors must not break transcript display
    }
  }
}

export function downsampleToPcm16(samples: Float32Array, inputRate: number, targetRate = 16000): Int16Array {
  if (inputRate === targetRate) {
    const out = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      const clamped = Math.max(-1, Math.min(1, samples[i]));
      out[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
    }
    return out;
  }
  const ratio = inputRate / targetRate;
  const newLength = Math.floor(samples.length / ratio);
  const out = new Int16Array(newLength);
  for (let i = 0; i < newLength; i++) {
    const idx = Math.min(samples.length - 1, Math.floor(i * ratio));
    const clamped = Math.max(-1, Math.min(1, samples[idx]));
    out[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  return out;
}
