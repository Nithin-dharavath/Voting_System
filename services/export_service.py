import csv
import io
import logging

from services.election_service import get_election_by_id, get_election_results

logger = logging.getLogger(__name__)


def export_results_csv(election_id: int) -> str | None:
    election = get_election_by_id(election_id)
    if not election:
        return None

    results, total_votes = get_election_results(election_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Candidate Name", "Department", "Academic Year", "Votes", "Percentage"])
    for r in results:
        writer.writerow(
            [
                r["candidate_name"],
                r["department"],
                r["academic_year"],
                r["vote_count"],
                f"{r['percentage']:.1f}%",
            ]
        )
    writer.writerow([])
    writer.writerow(["Total Votes", total_votes])

    return output.getvalue()


def export_results_pdf(election_id: int) -> bytes | None:
    election = get_election_by_id(election_id)
    if not election:
        return None

    results, total_votes = get_election_results(election_id)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Election Results: {election['title']}", styles["Title"]))
        story.append(Spacer(1, 0.25 * inch))

        if election.get("description"):
            story.append(Paragraph(election["description"], styles["Normal"]))
            story.append(Spacer(1, 0.25 * inch))

        story.append(Paragraph(f"Total Votes: {total_votes}", styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        data = [["Rank", "Candidate", "Department", "Votes", "Percentage"]]
        for i, r in enumerate(results, 1):
            data.append(
                [
                    str(i),
                    r["candidate_name"],
                    r.get("department", ""),
                    str(r["vote_count"]),
                    f"{r['percentage']:.1f}%",
                ]
            )

        table = Table(data, colWidths=[0.5 * inch, 2 * inch, 1.5 * inch, 0.8 * inch, 0.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), "#0f172a"),
                    ("TEXTCOLOR", (0, 0), (-1, 0), "#ffffff"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, "#e2e8f0"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), ["#ffffff", "#f8fafc"]),
                ]
            )
        )
        story.append(table)

        doc.build(story)
        return buffer.getvalue()
    except ImportError:
        logger.error("reportlab is not installed. Cannot generate PDF.")
        return None
    except Exception:
        logger.exception("Failed to generate PDF")
        return None
