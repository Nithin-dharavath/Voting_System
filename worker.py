import logging

from config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def run_worker():
    try:
        from redis import Redis
        from rq import Worker

        redis_conn = Redis.from_url(settings.redis_url)
        worker = Worker([settings.rq_queue_name], connection=redis_conn)
        logger.info(
            "RQ worker starting on queue '%s' (Redis: %s)",
            settings.rq_queue_name,
            settings.redis_url,
        )
        worker.work()
    except ImportError:
        logger.error("rq or redis not installed. Install with: pip install rq redis")
    except Exception:
        logger.exception("RQ worker failed to start")


if __name__ == "__main__":
    run_worker()
