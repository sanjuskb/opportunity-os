"""Pure-Python ATS-clean PDF resume renderer powered by fpdf2."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fpdf import FPDF

_UNICODE_REPLACEMENTS = str.maketrans(
    {
        "\u2013": "-",
        "\u2014": "--",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
        "\u2192": "->",
        "\u20b9": "INR ",
    }
)


def _pdf_safe_text(value: Any) -> str:
    raw = str(value or "").translate(_UNICODE_REPLACEMENTS)
    return raw.encode("latin-1", "replace").decode("latin-1")


def render_resume_pdf(title: str, content: dict[str, Any]) -> bytes:
    """Render structured resume content into valid ATS-readable PDF bytes."""
    from fpdf import FPDF

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    raw_profile = content.get("profile")
    profile: dict[str, Any] = raw_profile if isinstance(raw_profile, dict) else {}
    full_name = profile.get("full_name") or content.get("full_name") or title or "Student Resume"
    headline_parts = [
        str(part)
        for part in (
            profile.get("degree"),
            profile.get("branch_or_specialization") or profile.get("branch"),
            f"Batch {profile['graduation_year']}" if profile.get("graduation_year") else None,
            f"CGPA {profile['cgpa']}" if profile.get("cgpa") is not None else None,
        )
        if part
    ]

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, _pdf_safe_text(full_name), new_x="LMARGIN", new_y="NEXT")

    if headline_parts:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(70, 80, 95)
        pdf.cell(0, 6, _pdf_safe_text(" | ".join(headline_parts)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    summary = content.get("summary") or content.get("tailored_summary")
    if isinstance(summary, str) and summary.strip():
        _add_section_header(pdf, "SUMMARY")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _pdf_safe_text(summary.strip()))

    skills = content.get("normalized_skills") or content.get("skills") or []
    if isinstance(skills, list) and skills:
        _add_section_header(pdf, "TECHNICAL SKILLS")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _pdf_safe_text(", ".join(str(s) for s in skills)))

    for section_key, label in [
        ("education", "EDUCATION"),
        ("experience", "EXPERIENCE"),
        ("projects", "PROJECTS"),
        ("certifications", "CERTIFICATIONS"),
        ("achievements", "ACHIEVEMENTS"),
        ("tailored_bullets", "GROUNDED ROLE HIGHLIGHTS"),
    ]:
        entries = content.get(section_key)
        if not isinstance(entries, list) or not entries:
            continue
        _add_section_header(pdf, label)
        pdf.set_font("Helvetica", "", 10)
        for item in entries:
            if isinstance(item, dict):
                line = " - ".join(
                    str(item[k])
                    for k in (
                        "title",
                        "name",
                        "institution",
                        "degree",
                        "organization",
                        "summary",
                        "text",
                        "claim",
                    )
                    if item.get(k)
                )
            else:
                line = str(item)
            if line.strip():
                pdf.multi_cell(0, 5, _pdf_safe_text(f"* {line.strip()}"))

    raw_out = pdf.output()
    return bytes(raw_out)


def _add_section_header(pdf: FPDF, title: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 76, 129)
    pdf.cell(0, 6, _pdf_safe_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 210, 225)
    y = pdf.get_y()
    pdf.line(10, y, 200, y)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
