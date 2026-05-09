from textwrap import wrap

from app.schemas import SummaryOut


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _lines(summary: SummaryOut) -> list[str]:
    lines = [
        "Role Screening Interview Report",
        f"Session ID: {summary.session_id}",
        f"Role: {summary.role}",
        f"Questions answered: {summary.total_questions}",
        "",
        "Profile Signals",
        f"Skills: {', '.join(summary.profile.skills) or 'None detected'}",
        f"Technologies: {', '.join(summary.profile.technologies) or 'None detected'}",
        f"Domains: {', '.join(summary.profile.domains) or 'None detected'}",
        f"Seniority signal: {summary.profile.seniority_signal}",
        "",
        "Strengths",
    ]
    lines.extend(f"- {item}" for item in summary.strengths)
    lines.append("")
    lines.append("Gaps")
    lines.extend(f"- {item}" for item in summary.gaps)
    lines.append("")
    lines.append("Sources Used")
    lines.extend(f"- {item}" for item in summary.source_coverage)
    lines.append("")
    lines.append("Stored Questions and Answers")
    for index, item in enumerate(summary.interactions, start=1):
        source_names = sorted({context.source for context in item.context})
        lines.extend(
            [
                "",
                f"Question {index}: {item.question}",
                f"Sources: {', '.join(source_names)}",
                f"Answer: {item.answer or 'Not answered'}",
                f"Feedback: {(item.feedback or {}).get('note', 'No feedback')}",
            ]
        )
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(wrap(line, width=96) or [""])
    return wrapped


def build_summary_pdf(summary: SummaryOut) -> bytes:
    pages = []
    lines = _lines(summary)
    for start in range(0, len(lines), 42):
        pages.append(lines[start : start + 42])

    objects: list[str] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

    for index, page_lines in enumerate(pages):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        text_ops = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
        for line in page_lines:
            text_ops.append(f"({_escape_pdf_text(line)}) Tj")
            text_ops.append("T*")
        text_ops.append("ET")
        stream = "\n".join(text_ops)
        objects.append(f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream")

    pdf = ["%PDF-1.4\n"]
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode("latin-1", errors="replace")) for part in pdf))
        pdf.append(f"{number} 0 obj\n{obj}\nendobj\n")
    xref_offset = sum(len(part.encode("latin-1", errors="replace")) for part in pdf)
    pdf.append(f"xref\n0 {len(objects) + 1}\n")
    pdf.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.append(f"{offset:010d} 00000 n \n")
    pdf.append(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF")
    return "".join(pdf).encode("latin-1", errors="replace")
