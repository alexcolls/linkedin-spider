"""Redis queue producer for distributing profile URLs to workers."""

import os
from typing import List, Optional

import redis
from redis import Redis, ConnectionPool

from linkedin_spider.utils.logger import logger


class QueueProducer:
    """Producer for pushing profile URLs to Redis queue."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_name: Optional[str] = None,
        dead_letter_queue: Optional[str] = None
    ):
        """
        Initialize queue producer.

        Args:
            redis_url: Redis connection URL. If None, reads from env.
            queue_name: Name of the main work queue
            dead_letter_queue: Name of the dead letter queue for failed URLs
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.queue_name = queue_name or os.getenv("QUEUE_NAME", "linkedin:urls")
        self.dead_letter_queue = dead_letter_queue or f"{self.queue_name}:dead"
        
        # Connection pool for efficiency
        self.pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=10,
            decode_responses=True
        )
        self.redis_client = Redis(connection_pool=self.pool)
        
        try:
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis producer connected (queue: {self.queue_name})")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def push_url(self, url: str, priority: int = 0) -> bool:
        """
        Push a single URL to the queue.

        Args:
            url: Profile URL to scrape
            priority: Priority score (higher = more priority). Default 0.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use sorted set for priority queue
            self.redis_client.zadd(self.queue_name, {url: priority})
            logger.debug(f"Pushed URL to queue: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to push URL {url}: {e}")
            return False

    def push_urls_batch(self, urls: List[str], priority: int = 0) -> int:
        """
        Push multiple URLs to the queue in batch.

        Args:
            urls: List of profile URLs
            priority: Priority score for all URLs

        Returns:
            Number of URLs successfully pushed
        """
        if not urls:
            return 0

        try:
            # Create mapping for batch insert
            url_dict = {url: priority for url in urls}
            
            # Batch push with pipeline for efficiency
            pipeline = self.redis_client.pipeline()
            pipeline.zadd(self.queue_name, url_dict)
            pipeline.execute()
            
            logger.info(f"✅ Pushed {len(urls)} URLs to queue")
            return len(urls)
            
        except Exception as e:
            logger.error(f"Failed to push URLs batch: {e}")
            return 0

    def push_urls_from_file(self, file_path: str, priority: int = 0) -> int:
        """
        Read URLs from file and push to queue.

        Args:
            file_path: Path to file with URLs (one per line)
            priority: Priority score for URLs

        Returns:
            Number of URLs successfully pushed
        """
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            count = self.push_urls_batch(urls, priority)
            logger.info(f"✅ Loaded {count} URLs from {file_path}")
            return count
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return 0
        except Exception as e:
            logger.error(f"Failed to load URLs from file: {e}")
            return 0

    def get_queue_size(self) -> int:
        """
        Get number of URLs in the queue.

        Returns:
            Queue size
        """
        try:
            size = self.redis_client.zcard(self.queue_name)
            return size
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0

    def get_dead_letter_size(self) -> int:
        """
        Get number of URLs in dead letter queue.

        Returns:
            Dead letter queue size
        """
        try:
            size = self.redis_client.zcard(self.dead_letter_queue)
            return size
        except Exception as e:
            logger.error(f"Failed to get dead letter queue size: {e}")
            return 0

    def clear_queue(self) -> bool:
        """
        Clear all URLs from the main queue.

        Returns:
            True if successful
        """
        try:
            self.redis_client.delete(self.queue_name)
            logger.info("✅ Queue cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False

    def clear_dead_letter_queue(self) -> bool:
        """
        Clear dead letter queue.

        Returns:
            True if successful
        """
        try:
            self.redis_client.delete(self.dead_letter_queue)
            logger.info("✅ Dead letter queue cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear dead letter queue: {e}")
            return False

    def requeue_dead_letters(self, priority: int = 0) -> int:
        """
        Move URLs from dead letter queue back to main queue.

        Args:
            priority: Priority for requeued URLs

        Returns:
            Number of URLs requeued
        """
        try:
            # Get all URLs from dead letter queue
            dead_urls = self.redis_client.zrange(self.dead_letter_queue, 0, -1)
            
            if not dead_urls:
                logger.info("No dead letters to requeue")
                return 0
            
            # Push back to main queue
            count = self.push_urls_batch(list(dead_urls), priority)
            
            # Clear dead letter queue
            self.clear_dead_letter_queue()
            
            logger.info(f"✅ Requeued {count} URLs from dead letter queue")
            return count
            
        except Exception as e:
            logger.error(f"Failed to requeue dead letters: {e}")
            return 0

    def get_queue_stats(self) -> dict:
        """
        Get statistics about queues.

        Returns:
            Dictionary with queue statistics
        """
        return {
            'queue_name': self.queue_name,
            'queue_size': self.get_queue_size(),
            'dead_letter_queue': self.dead_letter_queue,
            'dead_letter_size': self.get_dead_letter_size(),
            'redis_url': self.redis_url.split('@')[-1],  # Hide credentials
        }

    def close(self):
        """Close Redis connections."""
        try:
            self.redis_client.close()
            self.pool.disconnect()
            logger.info("Redis producer connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")


# Global producer instance
_producer = None


def get_producer() -> QueueProducer:
    """
    Get or create global producer instance.

    Returns:
        QueueProducer instance
    """
    global _producer
    if _producer is None:
        _producer = QueueProducer()
    return _producer
