import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.rag_service import RAGService
from app.services.pdf_processor import PDFProcessor


router = APIRouter()


@router.post("/upload", tags=["documents"])
async def upload_document(file: UploadFile = File(...)):
    allowed_extensions = {".pdf", ".txt"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(allowed_extensions)}.",
        )

    file_path = f"temp{ext}"
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        with open(file_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    try:
        rag_service = RAGService()
        pdf_processor = PDFProcessor(file_path, rag_service)
        result = pdf_processor.process_pdf()
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return result