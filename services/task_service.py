import logging

from config import settings

logger = logging.getLogger(__name__)


def enqueue_export(election_id: int, format: str = "csv") -> str | None:
    try:
        from redis import Redis
        from rq import Queue

        redis_conn = Redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=redis_conn)
        from jobs.export_job import export_results

        job = queue.enqueue(export_results, election_id, format)
        logger.info("Enqueued export job %s for election %s format %s", job.id, election_id, format)
        return job.id
    except Exception:
        logger.exception("Failed to enqueue export job")
        return None


def get_export_result(job_id: str) -> dict | None:
    try:
        from services.cache_service import cache_get

        return cache_get(f"export:{job_id}")
    except Exception:
        logger.exception("Failed to get export result for job %s", job_id)
        return None


def get_job_status(job_id: str) -> dict:
    try:
        from redis import Redis
        from rq import Queue

        redis_conn = Redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=redis_conn)
        job = queue.fetch_job(job_id)
        if job is None:
            result = get_export_result(job_id)
            if result:
                return {"status": "completed", "result": result}
            return {"status": "not_found"}
        return {
            "status": job.get_status(),
            "meta": job.meta,
            "result": job.result,
            "enqueued_at": str(job.enqueued_at) if job.enqueued_at else None,
        }
    except Exception:
        logger.exception("Failed to get job status for %s", job_id)
        return {"status": "error"}
