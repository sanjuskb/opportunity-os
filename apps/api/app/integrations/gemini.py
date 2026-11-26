"""Google Gemini REST + Function Calling + Live API bidirectional WebSocket integration."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx
import websockets
from websockets.exceptions import WebSocketException

from app.core.config import settings

logger = logging.getLogger("opportunity_os.integrations.gemini")

SUPPORTED_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "te": "Telugu (తెలుగు)",
    "ta": "Tamil (தமிழ்)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "bn": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "hinglish": "Hinglish (Hindi-English conversational mix)",
}


def build_copilot_system_instruction(language: str = "en") -> str:
    lang_label = SUPPORTED_LANGUAGE_NAMES.get(language, "English")
    return (
        "You are NexteRaS Career Intelligence Copilot for Indian college students. "
        f"Respond warmly, concisely, and accurately in {lang_label}, preserving technical terms "
        "(Python, FastAPI, SQL, CGPA, React, AWS, ATS) in English script for clarity. "
        "Never invent opportunities, stipends, deadlines, or resume credentials; always query "
        "available platform tools when checking student eligibility, saved/discovered "
        "opportunities, skill gaps, Career Passport records, or applications."
    )


CAREER_TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "search_opportunities",
        "description": "Search active internships, hackathons, fellowships, scholarships, and jobs matching a query.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Role, skill, company, or location query.",
                },
                "opportunity_type": {
                    "type": "STRING",
                    "description": "Optional type filter: internship, full_time, fellowship, hackathon, scholarship.",
                },
                "limit": {"type": "INTEGER", "description": "Maximum results (1 to 10)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_eligibility",
        "description": "Evaluate deterministic eligibility and skill gaps for a specific opportunity ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "opportunity_id": {"type": "STRING", "description": "UUID of the opportunity."},
            },
            "required": ["opportunity_id"],
        },
    },
    {
        "name": "get_career_passport",
        "description": "Retrieve the authenticated student's education, CGPA, verified skills, and Career Passport items.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "list_applications",
        "description": "List the authenticated student's tracked applications and pending human approvals.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
]


@dataclass
class GeminiChatResult:
    reply: str
    provider: str
    model: str
    tool_calls_executed: list[dict[str, Any]] = field(default_factory=list)


class GeminiClient:
    """Typed async Google Gemini client supporting REST generation and function calling."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 12.0,
    ) -> None:
        self._api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self._model = model or settings.GEMINI_MODEL
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    @property
    def model(self) -> str:
        return self._model

    async def generate_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        candidates = [self._model]
        for fallback_model in ("gemini-3.8-flash", "gemini-3-flash-preview"):
            if fallback_model not in candidates:
                candidates.append(fallback_model)
        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for model_name in candidates:
                url = f"{self._base_url}/models/{model_name}:generateContent"
                try:
                    resp = await client.post(
                        url,
                        headers={"x-goog-api-key": self._api_key},
                        json=payload,
                    )
                    if resp.status_code in (404, 503):
                        last_exc = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code} for {model_name}",
                            request=resp.request,
                            response=resp,
                        )
                        continue
                    resp.raise_for_status()
                    data: dict[str, Any] = resp.json()
                    return data
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_exc = exc
                    continue
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Gemini generateContent failed without response")

    async def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        data = await self.generate_content(payload)
        return _extract_text_from_response(data)

    async def chat_with_tools(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        language: str = "en",
        tool_executor: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
        max_tool_hops: int = 3,
    ) -> GeminiChatResult:
        if not self._api_key:
            # Explicit unconfigured fallback (used only when no key is provided in local tests)
            fallback_reply = await self._offline_fallback_reply(
                user_message=user_message,
                language=language,
                tool_executor=tool_executor,
            )
            return GeminiChatResult(
                reply=fallback_reply,
                provider="offline-fallback",
                model="deterministic-local",
            )

        contents: list[dict[str, Any]] = []
        for msg in (history or [])[-8:]:
            role = "model" if msg.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": build_copilot_system_instruction(language)}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.35},
        }
        if tool_executor is not None:
            payload["tools"] = [{"functionDeclarations": CAREER_TOOL_DECLARATIONS}]

        executed_tools: list[dict[str, Any]] = []
        try:
            for _ in range(max_tool_hops):
                data = await self.generate_content(payload)
                candidate = (data.get("candidates") or [{}])[0]
                content = candidate.get("content") or {}
                parts = content.get("parts") or []
                fn_calls = [
                    p["functionCall"] for p in parts if isinstance(p, dict) and "functionCall" in p
                ]
                if not fn_calls or tool_executor is None:
                    text = _extract_text_from_response(data)
                    return GeminiChatResult(
                        reply=text or "I processed your request successfully.",
                        provider="gemini",
                        model=self._model,
                        tool_calls_executed=executed_tools,
                    )

                contents.append({"role": "model", "parts": parts})
                response_parts: list[dict[str, Any]] = []
                for call in fn_calls:
                    name = str(call.get("name", ""))
                    args = call.get("args") or {}
                    if not isinstance(args, dict):
                        args = {}
                    tool_output = await tool_executor(name, args)
                    executed_tools.append({"name": name, "args": args})
                    response_parts.append(
                        {
                            "functionResponse": {
                                "name": name,
                                "response": {"result": tool_output},
                            }
                        }
                    )
                contents.append({"role": "user", "parts": response_parts})
                payload["contents"] = contents

            final_data = await self.generate_content(payload)
            return GeminiChatResult(
                reply=_extract_text_from_response(final_data) or "Here is what I found for you.",
                provider="gemini",
                model=self._model,
                tool_calls_executed=executed_tools,
            )
        except Exception as exc:
            logger.warning(
                "Gemini API call degraded (%s); returning grounded assistant summary.",
                type(exc).__name__,
            )
            fallback_reply = await self._offline_fallback_reply(
                user_message=user_message,
                language=language,
                tool_executor=tool_executor,
            )
            return GeminiChatResult(
                reply=fallback_reply,
                provider="fallback-after-error",
                model=self._model,
                tool_calls_executed=executed_tools,
            )

    @staticmethod
    async def _offline_fallback_reply(
        *,
        user_message: str,
        language: str,
        tool_executor: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]] | None,
    ) -> str:
        lang_name = SUPPORTED_LANGUAGE_NAMES.get(language, language)
        if tool_executor is not None:
            search_res = await tool_executor(
                "search_opportunities", {"query": user_message, "limit": 3}
            )
            items = search_res.get("opportunities") or []
            if items:
                titles = ", ".join(str(item.get("title", "Opportunity")) for item in items[:3])
                return f"[{lang_name}] Found matching opportunities in NexteRaS catalog: {titles}."
        return f"[{lang_name}] NexteRaS Career Copilot is ready. Ask about internships, resume checks, or eligibility."


class GeminiLiveRelay:
    """Bidirectional WebSocket relay between NexteRaS client socket and Gemini BidiGenerateContent."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        ws_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self._ws_url = (ws_url or settings.GEMINI_LIVE_WEBSOCKET_URL).strip()
        self._model = model or settings.GEMINI_LIVE_MODEL

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._ws_url)

    def build_setup_payload(
        self, language: str = "en", enable_tools: bool = True
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "setup": {
                "model": f"models/{self._model}",
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}},
                    },
                },
                "systemInstruction": {
                    "parts": [{"text": build_copilot_system_instruction(language)}],
                },
                "inputAudioTranscription": {},
                "outputAudioTranscription": {},
            }
        }
        if enable_tools:
            payload["setup"]["tools"] = [{"functionDeclarations": CAREER_TOOL_DECLARATIONS}]
        return payload

    async def stream_session(
        self,
        *,
        client_send_json: Callable[[dict[str, Any]], Awaitable[None]],
        client_queue: asyncio.Queue[dict[str, Any] | None],
        language: str = "en",
        tool_executor: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
    ) -> None:
        url = f"{self._ws_url}?key={self._api_key}"
        try:
            async with websockets.connect(
                url, open_timeout=10, max_size=4 * 1024 * 1024
            ) as upstream:
                await upstream.send(
                    json.dumps(
                        self.build_setup_payload(
                            language=language, enable_tools=tool_executor is not None
                        )
                    )
                )
                setup_raw = await asyncio.wait_for(upstream.recv(), timeout=10)
                setup_msg = json.loads(setup_raw)
                await client_send_json(
                    {
                        "event": "live_connected",
                        "model": self._model,
                        "language": language,
                        "setupComplete": "setupComplete" in setup_msg,
                    }
                )

                async def _pump_client_to_upstream() -> None:
                    while True:
                        item = await client_queue.get()
                        if item is None:
                            return
                        kind = item.get("kind")
                        if kind == "pcm":
                            b64 = base64.b64encode(item["bytes"]).decode("ascii")
                            await upstream.send(
                                json.dumps(
                                    {
                                        "realtimeInput": {
                                            "mediaChunks": [
                                                {"mimeType": "audio/pcm;rate=16000", "data": b64}
                                            ]
                                        }
                                    }
                                )
                            )
                        elif kind == "text":
                            await upstream.send(
                                json.dumps(
                                    {
                                        "clientContent": {
                                            "turns": [
                                                {
                                                    "role": "user",
                                                    "parts": [{"text": str(item["text"])}],
                                                }
                                            ],
                                            "turnComplete": True,
                                        }
                                    }
                                )
                            )
                        elif kind == "interrupt":
                            await upstream.send(json.dumps({"realtimeInput": {"activityEnd": {}}}))

                async def _pump_upstream_to_client() -> None:
                    async for raw in upstream:
                        data = json.loads(raw) if isinstance(raw, (str, bytes)) else {}
                        if "toolCall" in data and tool_executor is not None:
                            calls = data["toolCall"].get("functionCalls") or []
                            responses: list[dict[str, Any]] = []
                            for call in calls:
                                name = str(call.get("name", ""))
                                args = call.get("args") or {}
                                result = await tool_executor(
                                    name, args if isinstance(args, dict) else {}
                                )
                                await client_send_json({"event": "tool_executed", "tool": name})
                                responses.append(
                                    {
                                        "id": call.get("id", name),
                                        "name": name,
                                        "response": {"result": result},
                                    }
                                )
                            await upstream.send(
                                json.dumps({"toolResponse": {"functionResponses": responses}})
                            )
                            continue

                        server_content = data.get("serverContent") or {}
                        if server_content.get("interrupted"):
                            await client_send_json({"event": "playback_cancelled"})
                        in_tx = (server_content.get("inputTranscription") or {}).get("text")
                        if in_tx:
                            await client_send_json({"event": "user_transcript", "text": in_tx})
                        out_tx = (server_content.get("outputTranscription") or {}).get("text")
                        if out_tx:
                            await client_send_json({"event": "ai_transcript", "text": out_tx})
                        model_turn = server_content.get("modelTurn") or {}
                        for part in model_turn.get("parts") or []:
                            if "text" in part:
                                await client_send_json(
                                    {"event": "ai_transcript", "text": part["text"]}
                                )
                            inline = part.get("inlineData") or {}
                            if inline.get("data"):
                                await client_send_json(
                                    {
                                        "event": "audio_delta",
                                        "mimeType": inline.get("mimeType", "audio/pcm;rate=24000"),
                                        "data": inline["data"],
                                    }
                                )
                        if server_content.get("turnComplete"):
                            await client_send_json({"event": "turn_complete"})

                await asyncio.gather(_pump_client_to_upstream(), _pump_upstream_to_client())
        except (WebSocketException, OSError, TimeoutError) as exc:
            logger.warning("Gemini Live session closed/degraded: %s", type(exc).__name__)
            await client_send_json(
                {
                    "event": "live_degraded",
                    "reason": type(exc).__name__,
                    "fallback": "rest_text_turn",
                }
            )


def _extract_text_from_response(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    texts: list[str] = []
    for cand in candidates:
        parts = ((cand.get("content") or {}).get("parts")) or []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return "\n".join(texts).strip()
