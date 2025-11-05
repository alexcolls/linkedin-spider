"""Database client for LinkedIn Spider distributed scraping."""

import os
import socket
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from sqlalchemy import exc
from sqlalchemy.dialects.postgresql import insert

from linkedin_spider.db.models import ProfileDB, ScrapeLog, init_db
from linkedin_spider.models.profile import Profile
from linkedin_spider.utils.logger import logger


class DatabaseClient:
    """Client for database operations with connection pooling."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database client.

        Args:
            database_url: PostgreSQL connection URL. If None, reads from env.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/linkedin_spider"
        )
        self.worker_id = os.getenv("HOSTNAME", socket.gethostname())
        
        # Initialize database
        try:
            self.engine, self.SessionLocal = init_db(self.database_url)
            logger.info(f"✅ Database client initialized (worker: {self.worker_id})")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy session with automatic commit/rollback
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def save_profile(self, profile: Profile) -> bool:
        """
        Save or update a profile in the database.

        Uses INSERT ... ON CONFLICT to handle deduplication automatically.

        Args:
            profile: Profile object to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Convert Profile to dict
                profile_data = {
                    'url': profile.url,
                    'name': profile.name,
                    'title': profile.title,
                    'company': profile.company,
                    'location': profile.location,
                    'about': profile.about,
                    'followers': profile.followers,
                    'scraped_at': profile.scraped_at,
                    'worker_id': self.worker_id,
                }

                # Use PostgreSQL INSERT ... ON CONFLICT for upsert
                stmt = insert(ProfileDB).values(**profile_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['url'],
                    set_={
                        'name': stmt.excluded.name,
                        'title': stmt.excluded.title,
                        'company': stmt.excluded.company,
                        'location': stmt.excluded.location,
                        'about': stmt.excluded.about,
                        'followers': stmt.excluded.followers,
                        'updated_at': datetime.utcnow(),
                        'worker_id': stmt.excluded.worker_id,
                    }
                )

                session.execute(stmt)
                logger.info(f"✅ Saved profile: {profile.url}")
                return True

        except exc.SQLAlchemyError as e:
            logger.error(f"Failed to save profile {profile.url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving profile {profile.url}: {e}")
            return False

    def save_profiles_batch(self, profiles: List[Profile]) -> int:
        """
        Save multiple profiles in a single transaction.

        Args:
            profiles: List of Profile objects

        Returns:
            Number of profiles successfully saved
        """
        if not profiles:
            return 0

        saved_count = 0
        try:
            with self.get_session() as session:
                for profile in profiles:
                    try:
                        profile_data = {
                            'url': profile.url,
                            'name': profile.name,
                            'title': profile.title,
                            'company': profile.company,
                            'location': profile.location,
                            'about': profile.about,
                            'followers': profile.followers,
                            'scraped_at': profile.scraped_at,
                            'worker_id': self.worker_id,
                        }

                        stmt = insert(ProfileDB).values(**profile_data)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=['url'],
                            set_={
                                'name': stmt.excluded.name,
                                'title': stmt.excluded.title,
                                'company': stmt.excluded.company,
                                'location': stmt.excluded.location,
                                'about': stmt.excluded.about,
                                'followers': stmt.excluded.followers,
                                'updated_at': datetime.utcnow(),
                                'worker_id': stmt.excluded.worker_id,
                            }
                        )

                        session.execute(stmt)
                        saved_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to save profile in batch {profile.url}: {e}")
                        continue

                logger.info(f"✅ Batch saved {saved_count}/{len(profiles)} profiles")
                return saved_count

        except Exception as e:
            logger.error(f"Batch save failed: {e}")
            return saved_count

    def log_scrape_attempt(
        self,
        url: str,
        status: str,
        error_message: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """
        Log a scrape attempt for monitoring.

        Args:
            url: Profile URL
            status: 'success', 'failed', or 'skipped'
            error_message: Error details if failed
            duration_seconds: Time taken to scrape

        Returns:
            True if logged successfully
        """
        try:
            with self.get_session() as session:
                log_entry = ScrapeLog(
                    url=url,
                    status=status,
                    error_message=error_message,
                    worker_id=self.worker_id,
                    duration_seconds=duration_seconds,
                )
                session.add(log_entry)
                return True

        except Exception as e:
            logger.error(f"Failed to log scrape attempt for {url}: {e}")
            return False

    def get_profile_count(self) -> int:
        """
        Get total number of profiles in database.

        Returns:
            Profile count
        """
        try:
            with self.get_session() as session:
                count = session.query(ProfileDB).count()
                return count
        except Exception as e:
            logger.error(f"Failed to get profile count: {e}")
            return 0

    def profile_exists(self, url: str) -> bool:
        """
        Check if a profile URL already exists in database.

        Args:
            url: Profile URL to check

        Returns:
            True if exists, False otherwise
        """
        try:
            with self.get_session() as session:
                exists = session.query(ProfileDB).filter(ProfileDB.url == url).first() is not None
                return exists
        except Exception as e:
            logger.error(f"Failed to check if profile exists {url}: {e}")
            return False

    def get_worker_stats(self) -> dict:
        """
        Get statistics for this worker.

        Returns:
            Dictionary with worker statistics
        """
        try:
            with self.get_session() as session:
                profiles_scraped = session.query(ProfileDB).filter(
                    ProfileDB.worker_id == self.worker_id
                ).count()

                logs = session.query(ScrapeLog).filter(
                    ScrapeLog.worker_id == self.worker_id
                ).all()

                total_attempts = len(logs)
                successful = len([log for log in logs if log.status == 'success'])
                failed = len([log for log in logs if log.status == 'failed'])

                return {
                    'worker_id': self.worker_id,
                    'profiles_scraped': profiles_scraped,
                    'total_attempts': total_attempts,
                    'successful': successful,
                    'failed': failed,
                    'success_rate': f"{(successful/total_attempts*100):.1f}%" if total_attempts > 0 else "N/A",
                }

        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {'worker_id': self.worker_id, 'error': str(e)}

    def close(self):
        """Close database connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database client instance (initialized when needed)
_db_client = None


def get_db_client() -> DatabaseClient:
    """
    Get or create global database client instance.

    Returns:
        DatabaseClient instance
    """
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client
