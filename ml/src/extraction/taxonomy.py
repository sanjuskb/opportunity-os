"""Canonical skill taxonomy, academic degree/branch aliases, and word-boundary matchers."""

from __future__ import annotations

import re

# Mapping of lowercase alias -> (canonical_name, skill_group)
# Groups: "programming_languages", "frameworks", "tools", "domain"
CANONICAL_SKILLS: dict[str, tuple[str, str]] = {
    "python": ("Python", "programming_languages"),
    "python3": ("Python", "programming_languages"),
    "c": ("C", "programming_languages"),
    "c++": ("C++", "programming_languages"),
    "cpp": ("C++", "programming_languages"),
    "java": ("Java", "programming_languages"),
    "javascript": ("JavaScript", "programming_languages"),
    "js": ("JavaScript", "programming_languages"),
    "typescript": ("TypeScript", "programming_languages"),
    "ts": ("TypeScript", "programming_languages"),
    "golang": ("Go", "programming_languages"),
    "go": ("Go", "programming_languages"),
    "rust": ("Rust", "programming_languages"),
    "sql": ("SQL", "programming_languages"),
    "verilog": ("Verilog", "programming_languages"),
    "systemverilog": ("SystemVerilog", "programming_languages"),
    "bash": ("Bash", "programming_languages"),
    "matlab": ("MATLAB", "programming_languages"),
    # Frameworks & Libraries
    "react": ("React", "frameworks"),
    "reactjs": ("React", "frameworks"),
    "react.js": ("React", "frameworks"),
    "next.js": ("Next.js", "frameworks"),
    "nextjs": ("Next.js", "frameworks"),
    "tailwind": ("Tailwind CSS", "frameworks"),
    "tailwind css": ("Tailwind CSS", "frameworks"),
    "tailwindcss": ("Tailwind CSS", "frameworks"),
    "fastapi": ("FastAPI", "frameworks"),
    "django": ("Django", "frameworks"),
    "flask": ("Flask", "frameworks"),
    "node.js": ("Node.js", "frameworks"),
    "nodejs": ("Node.js", "frameworks"),
    "express": ("Express.js", "frameworks"),
    "pytorch": ("PyTorch", "frameworks"),
    "torch": ("PyTorch", "frameworks"),
    "tensorflow": ("TensorFlow", "frameworks"),
    "scikit-learn": ("Scikit-learn", "frameworks"),
    "sklearn": ("Scikit-learn", "frameworks"),
    "sentence transformers": ("Sentence Transformers", "frameworks"),
    "sentence-transformers": ("Sentence Transformers", "frameworks"),
    "transformers": ("Transformers", "frameworks"),
    "hugging face": ("Hugging Face", "frameworks"),
    "huggingface": ("Hugging Face", "frameworks"),
    "langgraph": ("LangGraph", "frameworks"),
    "langchain": ("LangChain", "frameworks"),
    "pandas": ("Pandas", "frameworks"),
    "numpy": ("NumPy", "frameworks"),
    "opencv": ("OpenCV", "frameworks"),
    "ros2": ("ROS2", "frameworks"),
    "ros": ("ROS", "frameworks"),
    "xgboost": ("XGBoost", "frameworks"),
    "lightgbm": ("LightGBM", "frameworks"),
    "react native": ("React Native", "frameworks"),
    "three.js": ("Three.js", "frameworks"),
    # Tools & Platforms
    "postgresql": ("PostgreSQL", "tools"),
    "postgres": ("PostgreSQL", "tools"),
    "pgvector": ("pgvector", "tools"),
    "supabase": ("Supabase", "tools"),
    "redis": ("Redis", "tools"),
    "docker": ("Docker", "tools"),
    "kubernetes": ("Kubernetes", "tools"),
    "k8s": ("Kubernetes", "tools"),
    "git": ("Git", "tools"),
    "github": ("GitHub", "tools"),
    "github actions": ("GitHub Actions", "tools"),
    "playwright": ("Playwright", "tools"),
    "linux": ("Linux", "tools"),
    "aws": ("AWS", "tools"),
    "gcp": ("GCP", "tools"),
    "terraform": ("Terraform", "tools"),
    "figma": ("Figma", "tools"),
    "onnx": ("ONNX Runtime", "tools"),
    "onnx runtime": ("ONNX Runtime", "tools"),
    "spacy": ("spaCy", "tools"),
    "pydantic": ("Pydantic", "tools"),
    "graphql": ("GraphQL", "tools"),
    "wireshark": ("Wireshark", "tools"),
    "stm32": ("STM32", "tools"),
    "esp32": ("ESP32", "tools"),
    "rtos": ("RTOS", "tools"),
    "fpga": ("FPGA", "tools"),
    # Technical Domains
    "machine learning": ("Machine Learning", "domain"),
    "deep learning": ("Deep Learning", "domain"),
    "natural language processing": ("NLP", "domain"),
    "nlp": ("NLP", "domain"),
    "computer vision": ("Computer Vision", "domain"),
    "rest api": ("REST APIs", "domain"),
    "rest apis": ("REST APIs", "domain"),
    "distributed systems": ("Distributed Systems", "domain"),
    "embedded systems": ("Embedded Systems", "domain"),
    "slam": ("SLAM", "domain"),
    "asr": ("ASR", "domain"),
}

DEGREE_ALIASES: dict[str, str] = {
    "b.tech": "B.Tech",
    "btech": "B.Tech",
    "bachelor of technology": "B.Tech",
    "b.e": "B.E.",
    "b.e.": "B.E.",
    "bachelor of engineering": "B.E.",
    "m.tech": "M.Tech",
    "mtech": "M.Tech",
    "master of technology": "M.Tech",
    "dual degree": "Dual Degree",
    "mca": "MCA",
    "b.sc": "B.Sc",
    "bsc": "B.Sc",
}

EQUIVALENT_DEGREES: dict[str, set[str]] = {
    "b.tech": {"b.tech", "b.e.", "dual degree"},
    "b.e.": {"b.tech", "b.e.", "dual degree"},
    "dual degree": {"b.tech", "b.e.", "m.tech", "dual degree"},
    "m.tech": {"m.tech", "dual degree"},
    "mca": {"mca"},
    "b.sc": {"b.sc"},
}

BRANCH_ALIASES: dict[str, str] = {
    "cse": "Computer Science & Engineering",
    "computer science & engineering": "Computer Science & Engineering",
    "computer science and engineering": "Computer Science & Engineering",
    "computer science": "Computer Science & Engineering",
    "cs": "Computer Science & Engineering",
    "it": "Information Technology",
    "information technology": "Information Technology",
    "ai & ml": "Artificial Intelligence & Machine Learning",
    "ai & machine learning": "Artificial Intelligence & Machine Learning",
    "data science": "Data Science & AI",
    "ece": "Electronics & Communication Engineering",
    "electronics & communication": "Electronics & Communication Engineering",
    "electronics and communication": "Electronics & Communication Engineering",
    "eee": "Electrical & Electronics Engineering",
    "electrical & electronics": "Electrical & Electronics Engineering",
    "mechanical": "Mechanical Engineering",
}


def normalize_skill(raw_skill: str) -> tuple[str, str] | None:
    """Return canonical (skill_name, category) ONLY for recognized skills cleanly."""
    key = " ".join(raw_skill.strip().lower().split())
    if key in CANONICAL_SKILLS:
        return CANONICAL_SKILLS[key]
    return None


def deduplicate_skills(items: list[str]) -> list[str]:
    """Normalize known aliases cleanly while preserving custom skills once case-insensitively."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        norm = normalize_skill(raw)
        label = norm[0] if norm else " ".join(raw.strip().split())
        if not label:
            continue
        lk = label.lower()
        if lk not in seen:
            seen.add(lk)
            out.append(label)
    return out


def find_skills_with_evidence(text: str) -> list[tuple[str, str, str]]:
    """
    Match ONLY explicit word/symbol boundary mentions in source text.
    Does not infer unmentioned skills. Avoids matching plain English 'go' unless uppercase/skill-listed.
    """
    matches: dict[str, tuple[str, str, str]] = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Sort longest aliases first so "next.js" / "react native" win over single tokens
    sorted_aliases = sorted(CANONICAL_SKILLS.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        canonical, group = CANONICAL_SKILLS[alias]
        if canonical in matches:
            continue

        # Handle tricky short English tokens like 'go', 'c', 'ts', 'js' strictly
        if alias == "go":
            pattern = re.compile(r"(?:(?<=[:,/\s])Go(?=[:,/\s.])|\bGolang\b)")
        elif alias == "c":
            pattern = re.compile(r"(?:^|[\s,|/])C(?=$|[\s,|/])")
        else:
            escaped = re.escape(alias)
            pattern = re.compile(rf"(?<![A-Za-z0-9_+#]){escaped}(?![A-Za-z0-9_+#])", re.IGNORECASE)

        for ln in lines:
            if pattern.search(ln):
                matches[canonical] = (canonical, group, ln[:180])
                break

    return list(matches.values())


def normalize_degree(raw_degree: str | None) -> str | None:
    if not raw_degree:
        return None
    low = " ".join(raw_degree.lower().strip().split())
    for k, canonical in DEGREE_ALIASES.items():
        if re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", low):
            return canonical
    return raw_degree.strip()


def normalize_branch(raw_branch: str | None) -> str | None:
    if not raw_branch:
        return None
    low = " ".join(raw_branch.lower().strip().split())
    for k, canonical in sorted(BRANCH_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", low):
            return canonical
    return raw_branch.strip()
