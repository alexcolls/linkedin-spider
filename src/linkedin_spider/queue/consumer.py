"""Redis queue consumer for worker nodes."""

import os
import time
from typing import Optional, Callable

import redis
from redis import Redis, ConnectionPool

from linkedin_spider.utils.logger import logger


class QueueConsumer:
    """Consumer for pulling profile URLs from Redis queue."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_name: Optional[str] = None,
        dead_letter_queue: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize queue consumer.

        Args:
            redis_url: Redis connection URL. If None, reads from env.
            queue_name: Name of the work queue
            dead_letter_queue: Name of dead letter queue for failed URLs
            max_retries: Maximum retry attempts before moving to dead letter
            retry_delay: Base delay in seconds between retries (exponential backoff)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.queue_name = queue_name or os.getenv("QUEUE_NAME", "linkedin:urls")
        self.dead_letter_queue = dead_letter_queue or f"{self.queue_name}:dead"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Retry tracking - url: retry_count
        self.retry_attempts = {}
        
        # Connection pool
        self.pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=5,
            decode_responses=True
        )
        self.redis_client = Redis(connection_pool=self.pool)
        
        try:
            self.redis_client.ping()
            logger.info(f"✅ Redis consumer connected (queue: {self.queue_name})")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def pop_url(self, timeout: int = 0) -> Optional[str]:
        """
        Pop next URL from queue (blocking operation).

        Args:
            timeout: Timeout in seconds (0 = block indefinitely)

        Returns:
            URL string or None if timeout
        """
        try:
            # BZPOPMAX - Block and pop highest priority item
            result = self.redis_client.bzpopmax(self.queue_name, timeout=timeout)
            
            if result:
                # Result format: (queue_name, url, score)
                url = result[1]
                logger.debug(f"Popped URL from queue: {url}")
                return url
            
            return None
            
        except redis.ConnectionError:
            logger.error("Redis connection lost")
            raise
        except Exception as e:
            logger.error(f"Failed to pop URL: {e}")
            return None

    def mark_success(self, url: str):
        """
        Mark URL as successfully processed.

        Args:
            url: Successfully processed URL
        """
        # Remove from retry tracking
        if url in self.retry_attempts:
            del self.retry_attempts[url]
        logger.debug(f"Marked as success: {url}")

    def mark_failure(self, url: str, error: Optional[str] = None) -> bool:
        """
        Mark URL as failed and handle retry logic.

        Args:
            url: Failed URL
            error: Optional error message

        Returns:
            True if URL should be retried, False if moved to dead letter
        """
        # Track retry attempts
        self.retry_attempts[url] = self.retry_attempts.get(url, 0) + 1
        attempt = self.retry_attempts[url]
        
        if attempt >= self.max_retries:
            # Max retries reached - move to dead letter queue
            self._move_to_dead_letter(url, error)
            del self.retry_attempts[url]
            logger.warning(f"Max retries reached for {url}, moved to dead letter queue")
            return False
        else:
            # Retry with exponential backoff
            retry_priority = time.time() + (self.retry_delay * (2 ** (attempt - 1)))
            self._requeue_url(url, retry_priority)
            logger.info(f"Requeued {url} for retry (attempt {attempt}/{self.max_retries})")
            return True

    def _requeue_url(self, url: str, priority: float):
        """
        Put URL back in queue with specified priority.

        Args:
            url: URL to requeue
            priority: Priority score (timestamp for delayed retry)
        """
        try:
            self.redis_client.zadd(self.queue_name, {url: priority})
        except Exception as e:
            logger.error(f"Failed to requeue URL {url}: {e}")

    def _move_to_dead_letter(self, url: str, error: Optional[str] = None):
        """
        Move failed URL to dead letter queue.

        Args:
            url: Failed URL
            error: Optional error message
        """
        try:
            # Store in dead letter queue with error info
            timestamp = time.time()
            self.redis_client.zadd(self.dead_letter_queue, {url: timestamp})
            
            # Optionally store error details in separate hash
            if error:
                error_key = f"{self.dead_letter_queue}:errors"
                self.redis_client.hset(error_key, url, error)
                
        except Exception as e:
            logger.error(f"Failed to move URL to dead letter queue {url}: {e}")

    def consume_loop(
        self,
        process_func: Callable[[str], bool],
        batch_size: int = 1,
        poll_interval: int = 5
    ):
        """
        Main consumer loop - continuously process URLs from queue.

        Args:
            process_func: Function to process each URL. Should return True on success.
            batch_size: Number of URLs to process before checking queue again
            poll_interval: Seconds to wait if queue is empty
        """
        logger.info(f"Starting consumer loop (batch_size={batch_size})")
        
        processed_count = 0
        
        try:
            while True:
                # Pop URL from queue
                url = self.pop_url(timeout=poll_interval)
                
                if url is None:
                    # Queue is empty, wait and continue
                    logger.debug("Queue empty, waiting...")
                    time.sleep(poll_interval)
                    continue
                
                # Process URL
                try:
                    success = process_func(url)
                    
                    if success:
                        self.mark_success(url)
                        processed_count += 1
                        logger.info(f"✅ Processed successfully ({processed_count} total): {url}")
                    else:
                        self.mark_failure(url, "Processing returned False")
                        logger.warning(f"⚠️ Processing failed: {url}")
                        
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    self.mark_failure(url, error_msg)
                    logger.error(f"❌ Error processing {url}: {error_msg}")
                
        except KeyboardInterrupt:
            logger.info(f"Consumer loop interrupted. Processed {processed_count} URLs.")
            raise
        except Exception as e:
            logger.error(f"Consumer loop crashed: {e}")
            raise

    def get_queue_size(self) -> int:
        """Get current queue size."""
        try:
            return self.redis_client.zcard(self.queue_name)
        except Exception:
            return 0

    def close(self):
        """Close Redis connections."""
        try:
            self.redis_client.close()
            self.pool.disconnect()
            logger.info("Redis consumer connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")


# Global consumer instance
_consumer = None


def get_consumer() -> QueueConsumer:
    """
    Get or create global consumer instance.

    Returns:
        QueueConsumer instance
    """
    global _consumer
    if _consumer is None:
        _consumer = QueueConsumer()
    return _consumer
