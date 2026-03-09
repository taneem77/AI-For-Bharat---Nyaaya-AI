"""
report_generator.py — PDF eligibility report generation for Nyaaya.ai

Uses fpdf (1.7.2) for PDF generation. All text sanitized for latin-1 encoding.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


_UNICODE_MAP = {
    '\u2014': '-',   # em-dash
    '\u2013': '-',   # en-dash
    '\u2018': "'",   # left single quote
    '\u2019': "'",   # right single quote
    '\u201c': '"',   # left double quote
    '\u201d': '"',   # right double quote
    '\u2026': '...',  # ellipsis
    '\u20b9': 'Rs.',  # rupee sign
    '\u2022': '*',   # bullet
    '\u00a0': ' ',   # non-breaking space
}

_UNICODE_RE = re.compile('|'.join(re.escape(k) for k in _UNICODE_MAP))


def _s(text) -> str:
    """Sanitize text for latin-1 encoding (fpdf 1.7.2 limitation)."""
    text = str(text)
    text = _UNICODE_RE.sub(lambda m: _UNICODE_MAP[m.group()], text)
    return text.encode('latin-1', errors='replace').decode('latin-1')


def generate_pdf_report(profile: dict[str, Any], results: dict[str, Any]) -> bytes:
    """Generate a PDF eligibility report. Returns PDF bytes."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1 — Summary
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Nyaaya.ai - Eligibility Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')}", ln=True, align="C")
    pdf.ln(8)

    # User info
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Your Profile", ln=True)
    pdf.set_font("Helvetica", "", 11)

    profile_fields = [
        ("Age", profile.get("age", "-")),
        ("State", profile.get("state", "-")),
        ("District", profile.get("district", "-")),
        ("Income", f"Rs.{profile.get('income', 0):,}"),
        ("Marital Status", str(profile.get("marital_status", "-")).replace("_", " ").title()),
        ("Dependents", profile.get("dependents", 0)),
        ("Rural/Urban", "Rural" if profile.get("is_rural", True) else "Urban"),
    ]
    for label, val in profile_fields:
        pdf.cell(60, 7, f"{label}:", ln=False)
        pdf.cell(0, 7, _s(val), ln=True)
    pdf.ln(5)

    # Nyaaya Score
    summary = results.get("summary", {})
    score_data = summary.get("nyaaya_score", {})
    if score_data:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Nyaaya Score", ln=True)
        pdf.set_font("Helvetica", "B", 28)
        pdf.cell(40, 15, f"{score_data.get('score', 0)}/100")
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 15, f"  Grade {_s(score_data.get('grade', '-'))}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, _s(score_data.get("interpretation", "")), ln=True)
        pdf.ln(5)

    # Summary stats
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(80, 7, f"Eligible Schemes: {summary.get('schemes_count', 0)}", ln=False)
    pdf.cell(0, 7, f"Monthly Benefit: Rs.{summary.get('total_monthly_benefit', 0):,}", ln=True)
    pdf.cell(0, 7, f"First Year Total: Rs.{summary.get('first_year_total', 0):,}", ln=True)
    pdf.ln(5)

    # Page 2 — Eligible Schemes
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Eligible Schemes", ln=True)
    pdf.ln(3)

    eligible = [s for s in results.get("eligible_schemes", []) if s.get("eligible")]
    for scheme in eligible:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _s(scheme.get("scheme_name", "")), ln=True)
        pdf.set_font("Helvetica", "", 10)

        monthly = scheme.get("benefit_monthly", 0)
        onetime = scheme.get("benefit_onetime", 0)
        benefit_parts = []
        if monthly > 0:
            benefit_parts.append(f"Rs.{monthly:,}/month")
        if onetime > 0:
            benefit_parts.append(f"Rs.{onetime:,} one-time")
        if benefit_parts:
            pdf.cell(0, 6, f"  Benefit: {', '.join(benefit_parts)}", ln=True)

        pdf.cell(0, 6, _s(f"  Processing: {scheme.get('processing_weeks', '-')} weeks | Approval: {round(scheme.get('approval_rate', 0) * 100)}%"), ln=True)
        pdf.cell(0, 6, _s(f"  Reason: {scheme.get('reason', '')[:90]}"), ln=True)

        docs = scheme.get("required_documents", [])
        if docs:
            pdf.cell(0, 6, _s(f"  Documents: {', '.join(d.replace('_', ' ').title() for d in docs)}"), ln=True)
        pdf.ln(3)

    # Ineligible schemes
    ineligible = [s for s in results.get("eligible_schemes", []) if not s.get("eligible")]
    if ineligible:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Not Eligible", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for scheme in ineligible:
            pdf.cell(0, 6, _s(f"  {scheme.get('scheme_name', '')} - {scheme.get('reason', '')[:80]}"), ln=True)
        pdf.ln(3)

    # Page 3 — Strategy
    strategy = results.get("strategy", [])
    if strategy:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Application Strategy", ln=True)
        pdf.ln(3)

        for step in strategy:
            sid = step.get("scheme_id", "")
            scheme = next((s for s in eligible if s.get("scheme_id") == sid), {})
            name = scheme.get("scheme_name", sid.replace("_", " ").title())

            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, _s(f"Step {step.get('rank', '-')}: {name}"), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, _s(f"  Apply Week {step.get('apply_week', '-')} | Benefit: Rs.{step.get('total_benefit', 0):,}/yr | {step.get('timeline_weeks', '-')} weeks"), ln=True)
            pdf.cell(0, 6, _s(f"  {step.get('reasoning', '')[:100]}"), ln=True)
            pdf.ln(2)

    # Document checklist
    all_docs: list[str] = []
    seen: set[str] = set()
    for scheme in eligible:
        for doc in scheme.get("required_documents", []):
            if doc not in seen:
                all_docs.append(doc)
                seen.add(doc)

    if all_docs:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Document Checklist", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for i, doc in enumerate(all_docs, 1):
            pdf.cell(0, 6, _s(f"  [ ] {i}. {doc.replace('_', ' ').title()}"), ln=True)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "This report is generated by Nyaaya.ai for informational purposes.", ln=True)
    pdf.cell(0, 6, "Please verify eligibility at your nearest government office or CSC.", ln=True)

    output = pdf.output(dest='S')
    # fpdf2 returns bytearray, fpdf 1.7.2 returns str
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return output.encode('latin-1')
