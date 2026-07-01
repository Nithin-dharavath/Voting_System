import logging

from rq import get_current_job

logger = logging.getLogger(__name__)


def export_results(election_id: int, format: str = "csv") -> dict:
    job = get_current_job()
    job_id = job.id if job else None
    logger.info("Export job %s started: election %s format %s", job_id, election_id, format)

    try:
        if format == "csv":
            from services.cache_service import cache_set
            from services.export_service import export_results_csv

            csv_data = export_results_csv(election_id)
            if csv_data is None:
                return {"error": "Election not found"}
            cache_key = f"export:{job_id}"
            cache_set(
                cache_key, {"format": "csv", "data": csv_data, "election_id": election_id}, ttl=600
            )
            return {"success": True, "election_id": election_id, "format": "csv", "job_id": job_id}

        elif format == "pdf":
            from services.cache_service import cache_set
            from services.export_service import export_results_pdf

            pdf_data = export_results_pdf(election_id)
            if pdf_data is None:
                return {"error": "Election not found or PDF generation failed"}
            import base64

            cache_key = f"export:{job_id}"
            encoded = base64.b64encode(pdf_data).decode("ascii")
            cache_set(
                cache_key, {"format": "pdf", "data": encoded, "election_id": election_id}, ttl=600
            )
            return {"success": True, "election_id": election_id, "format": "pdf", "job_id": job_id}

        else:
            return {"error": f"Unsupported format: {format}"}
    except Exception:
        logger.exception("Export job %s failed", job_id)
        return {"error": "Export failed"}
