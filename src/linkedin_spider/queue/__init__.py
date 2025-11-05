"""Queue module for distributed work distribution."""

from linkedin_spider.queue.producer import QueueProducer, get_producer
from linkedin_spider.queue.consumer import QueueConsumer, get_consumer

__all__ = [
    'QueueProducer',
    'get_producer',
    'QueueConsumer',
    'get_consumer',
]
