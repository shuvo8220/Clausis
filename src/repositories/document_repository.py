

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ..database.models import Document, DocumentStatusEnum

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[Document]):
    """Repository for document-specific operations"""
    
    def __init__(self, session: Session):
        super().__init__(Document, session)
    
    def get_by_status(self, status: DocumentStatusEnum) -> List[Document]:
        """Get all documents with a specific status"""
        try:
            return self.session.query(Document).filter(
                Document.status == status
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching documents by status: {e}")
            raise
    
    def get_by_filename(self, filename: str) -> Optional[Document]:
        """Get document by filename"""
        try:
            return self.session.query(Document).filter(
                Document.filename == filename
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching document by filename: {e}")
            raise
    
    def get_ready_documents(self) -> List[Document]:
        """Get all documents that are ready for processing"""
        return self.get_by_status(DocumentStatusEnum.READY)
    
    def update_status(self, id: str, status: DocumentStatusEnum) -> Optional[Document]:
        """Update document status"""
        return self.update(id, status=status)
