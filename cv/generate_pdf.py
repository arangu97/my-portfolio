from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
MD_PATH = ROOT / "inigo-aranguren-cv.md"
PDF_PATH = ROOT / "inigo-aranguren-cv.pdf"


def to_html(text: str) -> str:
    """Minimal markdown-to-reportlab conversion for this CV."""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2">\1</link>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def parse_cv(markdown: str) -> dict:
    lines = [line.rstrip() for line in markdown.splitlines()]
    i = 0

    while i < len(lines) and not lines[i].strip():
        i += 1
    name = lines[i].lstrip("# ").strip() if i < len(lines) else ""
    i += 1

    contact = []
    while i < len(lines) and not lines[i].startswith("## "):
        line = lines[i].strip()
        if line:
            contact.append(line.replace("  ", ""))
        i += 1

    sections: dict[str, list] = {}
    current_section = None
    current_entry = None
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections[current_section] = []
            current_entry = None
        elif line.startswith("### ") and current_section:
            current_entry = {"title": line[4:].strip(), "date": "", "bullets": [], "notes": []}
            sections[current_section].append(current_entry)
        elif line.startswith("- ") and current_section:
            if current_entry is None:
                sections[current_section].append({"title": "", "date": "", "bullets": [line[2:].strip()], "notes": []})
            else:
                current_entry["bullets"].append(line[2:].strip())
        elif line.strip().startswith("**") and line.strip().endswith("**") and current_entry:
            current_entry["date"] = line.strip().strip("*").strip()
        elif line.strip():
            if current_entry is None:
                sections[current_section].append({"title": "", "date": "", "bullets": [], "notes": [line.strip()]})
            else:
                current_entry["notes"].append(line.strip())
        i += 1

    return {"name": name, "contact": contact, "sections": sections}


def extract_contact_fields(contact_lines: list[str]) -> dict:
    role = contact_lines[0] if contact_lines else ""
    location = ""
    email = ""
    linkedin = ""
    for line in contact_lines[1:]:
        if "@" in line and not email:
            email = line
        elif "[LinkedIn]" in line and not linkedin:
            linkedin = line
        elif not location:
            location = line
    return {"role": role, "location": location, "email": email, "linkedin": linkedin}


def linkedin_link_parts(linkedin_markdown: str) -> tuple[str, str]:
    match = re.search(r"\(([^)]+)\)", linkedin_markdown)
    if not match:
        return linkedin_markdown.strip(), "LinkedIn"
    href = match.group(1).strip()
    label = "LinkedIn"
    return href, label


def resolve_profile_image() -> Path | None:
    local_image = ROOT.parent / "assets" / "profile.png"
    if local_image.exists():
        return local_image

    index_path = ROOT.parent / "index.html"
    if not index_path.exists():
        return None

    html = index_path.read_text(encoding="utf-8")
    match = re.search(r'src="([^"]+DSCF4333[^"]+\.png)"', html)
    if not match:
        return None

    src = Path(match.group(1))
    if src.exists():
        return src
    return None


def build_pdf(data: dict) -> None:
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "Name",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=28,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "Contact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=2,
    )
    role_style_header = ParagraphStyle(
        "RoleHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.2,
        leading=14,
        textColor=colors.HexColor("#1F3A8A"),
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.2,
        textColor=colors.HexColor("#1F3A8A"),
        spaceBefore=10,
        spaceAfter=4,
    )
    role_style = ParagraphStyle(
        "Role",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#111827"),
        spaceBefore=5,
        spaceAfter=1,
    )
    date_style = ParagraphStyle(
        "Date",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.2,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=14,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=4,
    )

    contact_fields = extract_contact_fields(data["contact"])
    meta_parts = []
    if contact_fields["location"]:
        meta_parts.append(contact_fields["location"])
    if contact_fields["email"]:
        meta_parts.append(contact_fields["email"])
    if contact_fields["linkedin"]:
        linkedin_href, linkedin_label = linkedin_link_parts(contact_fields["linkedin"])
        meta_parts.append(f'<link href="{linkedin_href}"><u>{linkedin_label}</u></link>')
    meta_line = "   |   ".join(meta_parts)

    header_left = [Paragraph(data["name"], name_style)]
    if contact_fields["role"]:
        header_left.append(Paragraph(to_html(contact_fields["role"]), role_style_header))
    if meta_line:
        header_left.append(Paragraph(meta_line, contact_style))

    profile_image = resolve_profile_image()
    if profile_image:
        reader = ImageReader(str(profile_image))
        img_w, img_h = reader.getSize()
        max_w = 3.5 * cm
        max_h = 4.1 * cm
        scale = min(max_w / img_w, max_h / img_h)
        image = Image(str(profile_image), width=img_w * scale, height=img_h * scale)
        image.hAlign = "RIGHT"
        header_table = Table(
            [[header_left, image]],
            colWidths=[doc.width - 3.5 * cm, 3.5 * cm],
            hAlign="LEFT",
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story = [header_table]
    else:
        story = header_left

    story.append(Spacer(1, 8))
    story.append(HRFlowable(thickness=1, color=colors.HexColor("#D1D5DB"), width="100%"))
    story.append(Spacer(1, 4))

    for section_name, entries in data["sections"].items():
        if section_name.lower().startswith("formación"):
            story.append(PageBreak())
        story.append(Paragraph(section_name, section_style))
        story.append(HRFlowable(thickness=0.6, color=colors.HexColor("#E5E7EB"), width="100%"))
        story.append(Spacer(1, 2))

        for entry in entries:
            if entry["title"]:
                story.append(Paragraph(to_html(entry["title"]), role_style))
            if entry["date"]:
                story.append(Paragraph(to_html(entry["date"]), date_style))
            for note in entry["notes"]:
                story.append(Paragraph(to_html(note), body_style))
            if entry["bullets"]:
                story.append(
                    ListFlowable(
                        [
                            ListItem(
                                Paragraph(to_html(bullet), body_style),
                                leftIndent=10,
                            )
                            for bullet in entry["bullets"]
                        ],
                        bulletType="bullet",
                        leftIndent=12,
                        bulletFontName="Helvetica",
                        bulletFontSize=8,
                        bulletColor=colors.HexColor("#2563EB"),
                    )
                )
            story.append(Spacer(1, 3))

    doc.build(story)


if __name__ == "__main__":
    cv_data = parse_cv(MD_PATH.read_text(encoding="utf-8"))
    build_pdf(cv_data)
    print(PDF_PATH)
