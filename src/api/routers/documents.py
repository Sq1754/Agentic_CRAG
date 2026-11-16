"""Document upload and management router."""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.api.schemas import DocumentResponse
from src.config import settings
from src.db.database import get_db
from src.db.models import Document, User, WorkspaceMember

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/documents",
    tags=["Documents"],
)

ALLOWED_FILE_TYPES = {"pdf", "docx", "md", "txt"}
MAX_UPLOAD_BYTES = settings.max_upload_size_mb * 1024 * 1024


def _verify_membership(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    """Verify the user is a member of the workspace."""
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace.",
        )
    return member


def _get_file_extension(filename: str) -> str:
    """Extract and validate file extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(ALLOWED_FILE_TYPES)}",
        )
    return ext


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a document file (PDF, DOCX, MD, TXT) to be parsed, chunked, and indexed."""
    _verify_membership(db, workspace_id, current_user.id)

    # Validate file type
    file_type = _get_file_extension(file.filename or "unknown.txt")

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB.",
        )

    # Import services lazily to avoid circular imports at module load time
    from src.services.document_service import DocumentService

    doc_service = DocumentService(upload_dir=settings.upload_dir)

    # Save file to disk
    file_path = doc_service.save_upload_bytes(
        content=content,
        filename=file.filename or "document",
        workspace_id=str(workspace_id),
    )

    # Create document record in DB (status = "processing")
    import uuid

    doc_record = Document(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        uploaded_by=current_user.id,
        filename=file.filename or "document",
        file_type=file_type,
        file_size=len(content),
        storage_path=file_path,
        status="processing",
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # Process synchronously (parse → chunk → index into Qdrant)
    # In production, this would be an async task (Celery/ARQ)
    try:
        from src.api.main import app_state

        retriever = app_state.get("retriever")
        if not retriever:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Retrieval engine not initialized. Server is starting up.",
            )

        chunk_count = doc_service.process_and_index(
            db=db,
            retriever=retriever,
            document_id=str(doc_record.id),
            workspace_id=str(workspace_id),
            file_path=file_path,
            file_type=file_type,
        )
        db.refresh(doc_record)
    except Exception as e:
        doc_record.status = "failed"
        doc_record.error_message = str(e)[:500]
        db.commit()
        db.refresh(doc_record)

    return doc_record


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents in a workspace."""
    _verify_membership(db, workspace_id, current_user.id)

    documents = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    workspace_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific document's details."""
    _verify_membership(db, workspace_id, current_user.id)

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.workspace_id == workspace_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    workspace_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document and remove its vectors from the index."""
    member = _verify_membership(db, workspace_id, current_user.id)
    if member.role not in ("admin", "member"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot delete documents.")

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.workspace_id == workspace_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Remove file from disk
    if doc.storage_path and os.path.exists(doc.storage_path):
        os.remove(doc.storage_path)

    # Delete DB record (vector cleanup would require Qdrant delete by doc_id — future improvement)
    db.delete(doc)
    db.commit()
