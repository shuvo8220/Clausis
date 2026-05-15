"""
Base Repository - Generic CRUD operations
------------------------------------------
Follows Repository Pattern and DRY principle
"""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic repository providing common CRUD operations
    Reduces code duplication across repositories
    """
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.flush()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def get_by_id(self, id: str) -> Optional[T]:
        """Get a record by ID"""
        try:
            return self.session.query(self.model).filter(
                self.model.id == id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching {self.model.__name__} by ID: {e}")
            raise
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all records with optional pagination"""
        try:
            query = self.session.query(self.model).offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all {self.model.__name__}: {e}")
            raise
    
    def update(self, id: str, **kwargs) -> Optional[T]:
        """Update a record"""
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.session.flush()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    def delete(self, id: str) -> bool:
        """Delete a record"""
        try:
            instance = self.get_by_id(id)
            if instance:
                self.session.delete(instance)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise
    
    def count(self) -> int:
        """Count total records"""
        try:
            return self.session.query(self.model).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
