"""PDF export via reportlab — pure-Python wheels, works in python:3.13-slim.

Contains only our computed data, the disclosed formula, and citations; no
verbatim source text (docs/requirements.md copyright rule).
"""

import io

from app.chem.embeddings import parse_smiles


def report_pdf(payload: dict, project_id: int) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Molecule Scout report — project {project_id}",
    )
    styles = getSampleStyleSheet()
    h1, body, small = styles["Heading1"], styles["BodyText"], styles["BodyText"].clone(
        "small", fontSize=7.5, leading=9
    )
    story = [
        Paragraph("Molecule Scout — Candidate Report", h1),
        Paragraph(f"Project {project_id} · run {payload.get('pipeline_run_id')}", body),
        Spacer(1, 6),
        Paragraph(payload.get("disclaimer", ""), small),
        Spacer(1, 4),
        Paragraph(f"Rank formula: <b>{payload.get('formula', '')}</b> "
                  f"({payload.get('formula_version', '')})", small),
    ]
    cond = payload.get("conditioning_summary") or {}
    if cond:
        story.append(Paragraph(
            f"Conditioning: {cond.get('mode')} "
            f"{cond.get('seed_smiles') or ''} "
            f"{('sim ' + str(cond.get('similarity'))) if cond.get('similarity') is not None else ''}"
            f"{cond.get('reason') or ''}".strip(), small,
        ))
    if payload.get("terminal_reason"):
        story += [
            Spacer(1, 8),
            Paragraph(f"<b>No candidates.</b> {payload.get('summary', '')}", body),
        ]

    candidates = payload.get("candidates") or []
    if candidates:
        rows = [["#", "SMILES", "Score", "Affinity", "QED", "Source"]]
        for c in candidates:
            rows.append([
                str(c.get("rank")),
                (c.get("smiles") or "")[:28],
                _fmt(c.get("rank_score")),
                _fmt(c.get("affinity")),
                _fmt(c.get("qed")),
                c.get("rationale_source", ""),
            ])
        table = Table(rows, repeatRows=1, colWidths=[8 * mm, 62 * mm, 18 * mm, 18 * mm, 16 * mm, 34 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c2b3a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#3a4d61")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story += [Spacer(1, 8), table]

    for c in candidates:
        story.append(PageBreak())
        mol = parse_smiles(c.get("smiles") or "")
        drawing = _mol_image(mol) if mol is not None else None
        block = [
            Paragraph(f"Rank {c.get('rank')} — score {_fmt(c.get('rank_score'))}", styles["Heading2"]),
            Paragraph(f"<font face='Courier'>{c.get('smiles')}</font>", small),
            Paragraph(
                f"Affinity {_fmt(c.get('affinity'))} kcal/mol · QED {_fmt(c.get('qed'))} · "
                f"novelty {_fmt(c.get('novelty'))} · source <b>{c.get('rationale_source')}</b>",
                small,
            ),
            Spacer(1, 4),
        ]
        if drawing is not None:
            block.append(Image(drawing, width=70 * mm, height=50 * mm))
        block.append(Paragraph(c.get("rationale", ""), body))
        block.append(Spacer(1, 4))
        block.append(Paragraph(c.get("verification_note", ""), small))
        story.append(KeepTogether(block))

    doc.build(story)
    return buf.getvalue()


def _fmt(value) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "—"


def _mol_image(mol) -> io.BytesIO | None:
    """RDKit 2D depiction to PNG bytes for embedding."""
    try:
        from rdkit.Chem import Draw

        img = Draw.MolToImage(mol, size=(600, 400))
        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out
    except Exception:
        return None
