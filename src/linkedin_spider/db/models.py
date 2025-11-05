"""Database models for LinkedIn Spider."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, create_engine, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ProfileDB(Base):
    """
    Database model for LinkedIn profiles.
    
    Stores scraped profile data with automatic deduplication via unique URL constraint.
    """
    __tablename__ = "profiles"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Profile data
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    followers = Column(Integer, default=0)
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    worker_id = Column(String(100), nullable=True)  # Track which pod scraped it
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_company', 'company'),
        Index('idx_location', 'location'),
        Index('idx_scraped_at', 'scraped_at'),
    )
    
    def __repr__(self):
        return f"<ProfileDB(id={self.id}, name='{self.name}', url='{self.url}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'about': self.about,
            'followers': self.followers,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'worker_id': self.worker_id,
        }


class ScrapeLog(Base):
    """
    Log table for tracking scrape attempts and failures.
    
    Useful for debugging and monitoring worker performance.
    """
    __tablename__ = "scrape_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    worker_id = Column(String(100), nullable=True)
    attempt_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_status_attempt', 'status', 'attempt_at'),
        Index('idx_worker_attempt', 'worker_id', 'attempt_at'),
    )
    
    def __repr__(self):
        return f"<ScrapeLog(url='{self.url}', status='{self.status}')>"


def init_db(database_url: str):
    """
    Initialize database and create all tables.
    
    Args:
        database_url: SQLAlchemy database URL
        
    Returns:
        Tuple of (engine, SessionLocal)
    """
    engine = create_engine(
        database_url,
        pool_size=20,  # Connection pool for concurrent workers
        max_overflow=50,  # Additional connections during peaks
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections every hour
        echo=False,  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal
