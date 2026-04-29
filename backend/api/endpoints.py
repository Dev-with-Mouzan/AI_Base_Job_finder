import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from backend.services.resume_service import extract_text_from_pdf
from backend.services.job_service import fetch_job_listings
from backend.services.match_service import match_resume_with_jobs, get_resume_improvement_chat, extract_search_terms
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    resume_text: str
    message: str
    history: Optional[List[Dict[str, str]]] = []

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/match")
def match_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    logger.info("Received /match request")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        logger.info("Reading file...")
        file_bytes = file.file.read()
        logger.info(f"File size: {len(file_bytes)} bytes")
        
        logger.info("Extracting text from PDF...")
        resume_text = extract_text_from_pdf(file_bytes)
        logger.info(f"Extracted text length: {len(resume_text)}")
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        logger.info("Extracting search terms from resume...")
        search_terms = extract_search_terms(resume_text)
        logger.info(f"Generated search terms: {search_terms}")
        
        logger.info("Fetching live jobs...")
        jobs = fetch_job_listings(search_terms)
        logger.info(f"Fetched {len(jobs)} jobs")
        
        if not jobs:
            raise HTTPException(status_code=500, detail="Could not fetch job listings")
        
        logger.info("Starting match process...")
        matches = match_resume_with_jobs(resume_text, jobs)
        logger.info(f"Found {len(matches)} matches")
        
        return {
            "resume_text": resume_text,
            "jobs_found": len(jobs),
            "matches": matches
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def chat_resume(request: ChatRequest) -> Dict[str, Any]:
    logger.info("Received /chat request")
    try:
        response = get_resume_improvement_chat(
            request.resume_text, 
            request.message, 
            request.history
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health():
    return {"status": "healthy"}
