"""Non-destructive multilingual preprocessing, script detection, and career token preservation."""

from __future__ import annotations

import re
import unicodedata
from pydantic import BaseModel, Field

from ml.src.extraction.taxonomy import deduplicate_skills, find_skills_with_evidence

SCRIPT_RANGES: list[tuple[str, int, int]] = [
    ("hi_devanagari", 0x0900, 0x097F),
    ("bn_bengali", 0x0980, 0x09FF),
    ("gu_gujarati", 0x0A80, 0x0AFF),
    ("ta_tamil", 0x0B80, 0x0BFF),
    ("te_telugu", 0x0C00, 0x0C7F),
    ("kn_kannada", 0x0C80, 0x0CFF),
    ("ml_malayalam", 0x0D00, 0x0D7F),
]

MARATHI_DEVANAGARI_MARKERS = {
    "आहे",
    "आहेत",
    "मला",
    "माझे",
    "माझी",
    "करा",
    "करायची",
    "करायचे",
    "साठी",
    "पाहिजे",
    "नोकरी",
    "अर्ज",
    "येथे",
    "कसे",
    "मिळेल",
    "हवी",
    "तुम्ही",
    "काय",
    "किंवा",
    "आणि",
}

HINGLISH_MARKERS = {
    "chahiye", "hai", "hain", "mujhe", "mera", "meri", "karna", "sakta", "wala", "kaise", "milega", "bhi", "aur", "ke", "liye"
}


class PreprocessedMultilingualQuery(BaseModel):
    original_text: str
    normalized_text: str
    detected_scripts: list[str]
    predicted_locale: str
    preserved_technical_terms: list[str] = Field(default_factory=list)
    is_code_switched: bool = False


def detect_unicode_scripts(text: str) -> list[str]:
    scripts: set[str] = set()
    has_latin = False
    for ch in text:
        cp = ord(ch)
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            has_latin = True
            continue
        for name, lo, hi in SCRIPT_RANGES:
            if lo <= cp <= hi:
                scripts.add(name)
                break
    out = sorted(scripts)
    if has_latin:
        out.append("latin")
    return out or ["unknown"]


def infer_locale_hint(text: str, scripts: list[str]) -> tuple[str, bool]:
    script_map = {
        "hi_devanagari": "hi",
        "te_telugu": "te",
        "ta_tamil": "ta",
        "kn_kannada": "kn",
        "ml_malayalam": "ml",
        "bn_bengali": "bn",
        "gu_gujarati": "gu",
    }
    indic = [script_map[s] for s in scripts if s in script_map]
    if indic:
        locale = indic[0]
        if locale == "hi":
            devanagari_words = set(re.findall(r"[\u0900-\u097F]+", text))
            if devanagari_words & MARATHI_DEVANAGARI_MARKERS:
                locale = "mr"
        # Both native Indic script and English technical terms present -> code-switched
        return locale, ("latin" in scripts)

    tokens = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if tokens & HINGLISH_MARKERS:
        return "hinglish", True
    return "en", False


def preprocess_multilingual_query(text: str) -> PreprocessedMultilingualQuery:
    """
    Perform Unicode NFC normalization while preserving original text verbatim and
    retaining exact technical English tokens (e.g., Python, FastAPI, CGPA, ROS2).
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Multilingual query text must not be empty.")
    nfc = unicodedata.normalize("NFC", text)
    collapsed = " ".join(nfc.split())
    scripts = detect_unicode_scripts(collapsed)
    locale, code_switched = infer_locale_hint(collapsed, scripts)
    tech_terms = deduplicate_skills([c for c, _, _ in find_skills_with_evidence(collapsed)])
    return PreprocessedMultilingualQuery(
        original_text=text,
        normalized_text=collapsed,
        detected_scripts=scripts,
        predicted_locale=locale,
        preserved_technical_terms=tech_terms,
        is_code_switched=code_switched,
    )
