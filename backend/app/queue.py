from redis import Redis
from rq import Queue

from backend.app.config import get_settings


def get_queue() -> Queue:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    return Queue("campaigns", connection=connection)
