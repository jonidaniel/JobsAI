"""
Download API Routes.

Routes for downloading generated cover letter documents from S3.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse

from jobsai.utils.state_manager import get_presigned_s3_url
from jobsai.utils.logger import get_logger
from jobsai.api.utils.state_helpers import get_job_state_with_fallback

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download/{job_id}")
async def download_document(
    job_id: str,
    index: Optional[int] = Query(
        None, description="Document index (1-based) for multiple documents"
    ),
) -> JSONResponse:
    """Get presigned S3 URL(s) for downloading generated cover letter document(s).

    Returns presigned S3 URLs that allow the client to download documents directly
    from S3. Supports both single document (backward compatibility) and multiple
    documents. If index is provided, returns URL for that specific document.

    The presigned URLs are valid for 1 hour and include the correct Content-Type
    and Content-Disposition headers for proper browser handling.

    Args:
        job_id: Unique job identifier (UUID string) of the completed job.
        index: Optional document index (1-based) if multiple documents exist.
            If not provided and multiple documents exist, returns all URLs.

    Returns:
        JSONResponse with download information:
            Single document:
            {
                "download_url": "https://s3...presigned-url...",
                "filename": "20250115_143022_cover_letter.docx"
            }

            Multiple documents (if index not provided):
            {
                "download_urls": [
                    {"url": "https://s3...", "filename": "20250115_143022_cover_letter.docx"},
                    {"url": "https://s3...", "filename": "20250115_143022_cover_letter_2.docx"},
                    ...
                ],
                "count": 2
            }

            Multiple documents (if index provided):
            {
                "download_url": "https://s3...presigned-url...",
                "filename": "20250115_143022_cover_letter_2.docx"
            }

    Raises:
        HTTPException 404: If job_id is not found or index is out of range.
        HTTPException 400: If job status is not "complete" (documents not ready).

    Note:
        The client should use the download_url(s) to fetch documents directly
        from S3. This avoids API Gateway binary encoding issues and provides
        better download performance. URLs expire after 1 hour.
    """
    # Get state from DynamoDB with in-memory fallback
    state = get_job_state_with_fallback(job_id)

    if state["status"] != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document not ready. Status: {state['status']}",
        )

    result = state.get("result")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document result not available",
        )

    # Handle multiple documents
    if "filenames" in result and "s3_keys" in result:
        filenames = result.get("filenames", [])
        s3_keys = result.get("s3_keys", [])

        if index is not None:
            # Return specific document by index (1-based)
            if index < 1 or index > len(s3_keys):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document index {index} not found. Available: 1-{len(s3_keys)}",
                )
            s3_key = s3_keys[index - 1]
            filename = filenames[index - 1]
            presigned_url = get_presigned_s3_url(s3_key)
            if presigned_url:
                return JSONResponse(
                    content={
                        "download_url": presigned_url,
                        "filename": filename,
                    }
                )
        else:
            # Return all documents
            download_urls = []
            for s3_key, filename in zip(s3_keys, filenames):
                presigned_url = get_presigned_s3_url(s3_key)
                if presigned_url:
                    download_urls.append({"url": presigned_url, "filename": filename})

            if download_urls:
                return JSONResponse(
                    content={
                        "download_urls": download_urls,
                        "count": len(download_urls),
                    }
                )

    # Handle single document (backward compatibility)
    filename = result.get("filename", "cover_letter.docx")
    s3_key = result.get("s3_key")

    if s3_key:
        presigned_url = get_presigned_s3_url(s3_key)
        if presigned_url:
            logger.info(
                "Returning presigned S3 URL for download",
                extra={"extra_fields": {"job_id": job_id, "s3_key": s3_key}},
            )
            return JSONResponse(
                content={
                    "download_url": presigned_url,
                    "filename": filename,
                }
            )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No download URLs available",
    )
